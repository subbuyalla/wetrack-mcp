"""
HTTP client with automatic Bearer token injection and 401 auto-retry.
All tool modules call make_request() — never httpx directly.
"""

import httpx
from typing import Any
from .config import config
from .auth import auth_manager


async def make_request(
    method: str,
    path: str,
    json: dict | None = None,
    params: dict | None = None,
    data: dict | None = None,
    files: dict | None = None,
    auto_login: bool = True,
) -> dict:
    """
    Send an authenticated HTTP request to the WeTrack API.

    - Automatically injects Authorization: Bearer <token>
    - Sends browser-like headers to pass Vercel CORS/origin checks
    - On 401, attempts one auto-login then retries the request
    - Returns a normalized dict with success/message/data keys
    """
    # Ensure we have a token before the first real call
    if auto_login and not auth_manager.is_authenticated():
        try:
            await auth_manager.ensure_authenticated()
        except RuntimeError:
            # Not authenticated and no credentials — guide user to SSO
            return {
                "success": False,
                "authenticated": False,
                "message": (
                    "⚠️ You are not signed in to WeTrack. "
                    "Please call the 'wetrack_microsoft_sso_login' tool to sign in "
                    "with your Microsoft account. Your browser will open automatically."
                ),
                "action_required": "Call wetrack_microsoft_sso_login to authenticate via Microsoft SSO.",
            }

    # Remove None values from params
    if params:
        params = {k: v for k, v in params.items() if v is not None}

    # Build headers — always include browser-like origin to pass Vercel checks
    headers = {
        "Origin": config.BASE_URL,
        "Referer": config.BASE_URL + "/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
    if auth_manager.token:
        headers["Authorization"] = f"Bearer {auth_manager.token}"

    # Also send cookies if we have them (for cookie-based auth sessions)
    cookies = getattr(auth_manager, "_cookies", {})

    async with httpx.AsyncClient(
        base_url=config.BASE_URL,
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        response = await client.request(
            method=method.upper(),
            url=path,
            json=json,
            params=params,
            data=data,
            files=files,
            headers=headers,
            cookies=cookies,
        )

        # On 401 — attempt one re-login and retry (only if email/password available)
        if response.status_code == 401 and auto_login:
            from .config import config as cfg
            if cfg.EMAIL and cfg.PASSWORD:
                login_result = await auth_manager.sign_in()
                if login_result.get("success") and auth_manager.token:
                    headers["Authorization"] = f"Bearer {auth_manager.token}"
                    cookies = getattr(auth_manager, "_cookies", {})
                    response = await client.request(
                        method=method.upper(),
                        url=path,
                        json=json,
                        params=params,
                        data=data,
                        files=files,
                        headers=headers,
                        cookies=cookies,
                    )
            else:
                # SSO token expired — ask user to re-authenticate
                auth_manager.token = ""
                return {
                    "success": False,
                    "authenticated": False,
                    "message": (
                        "⚠️ Your WeTrack session has expired. "
                        "Please call 'wetrack_microsoft_sso_login' to sign in again."
                    ),
                    "action_required": "Call wetrack_microsoft_sso_login to re-authenticate.",
                }

    return _normalize_response(response)


def _normalize_response(response: httpx.Response) -> dict:
    """
    Turn any WeTrack API response into a consistent dict:
    { success: bool, status_code: int, data: Any, message: str }
    """
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text}

    is_success = 200 <= response.status_code < 300

    # If the API already returns { success, data, message } — preserve it
    if isinstance(body, dict) and "success" in body:
        body["status_code"] = response.status_code
        return body

    # Otherwise wrap it
    return {
        "success": is_success,
        "status_code": response.status_code,
        "data": body if is_success else None,
        "message": (
            body.get("message", body.get("error", "Unknown error"))
            if isinstance(body, dict) and not is_success
            else "OK"
        ),
    }
