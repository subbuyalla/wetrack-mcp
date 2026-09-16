"""Authentication manager — handles sign-in, token storage, and auto-refresh.

Authentication priority:
  1. SSO token set via wetrack_microsoft_sso_login (recommended for production)
  2. Pre-set WETRACK_TOKEN env var (optional, for scripted/headless use)
  3. Email + password via WETRACK_EMAIL / WETRACK_PASSWORD (optional fallback)

If none of the above are configured, tools will prompt the user to run
wetrack_microsoft_sso_login to authenticate via Microsoft SSO.
"""

import httpx
from .config import config


class AuthManager:
    """Manages JWT token lifecycle for WeTrack API calls."""

    def __init__(self):
        self._token: str = config.TOKEN  # pre-set token from env (optional)

    @property
    def token(self) -> str:
        return self.get_active_token()

    @token.setter
    def token(self, value: str):
        self._token = value

    def get_active_token(self) -> str:
        """Returns the active token: from request context (OAuth middleware) or stored token."""
        try:
            from mcp.server.auth.middleware.auth_context import auth_context_var
            user = auth_context_var.get(None)
            if user and hasattr(user, "access_token") and getattr(user.access_token, "token", None):
                return user.access_token.token
        except Exception:
            pass
        return self._token

    def is_authenticated(self) -> bool:
        return bool(self.get_active_token())

    async def sign_in(self, email: str | None = None, password: str | None = None) -> dict:
        """
        Authenticate with WeTrack and store the JWT token.
        Falls back to config credentials if email/password not provided.
        """
        email = email or config.EMAIL
        password = password or config.PASSWORD

        if not email or not password:
            raise ValueError(
                "WeTrack credentials not set. "
                "Add WETRACK_EMAIL and WETRACK_PASSWORD to your .env file."
            )

        # Use browser-like headers — the staging API (Vercel) rejects non-browser origins
        headers = {
            "Origin": config.BASE_URL,
            "Referer": config.BASE_URL + "/",
            "Content-Type": "application/json",
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

        async with httpx.AsyncClient(
            base_url=config.BASE_URL,
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            response = await client.post(
                "/api/auth/sign-in",
                json={"email": email, "password": password},
                headers=headers,
            )

        if response.status_code == 200:
            data = response.json()

            # Try extracting JWT from response body first (accessToken key)
            token = (
                data.get("accessToken")
                or data.get("token")
                or (data.get("data") or {}).get("accessToken")
                or (data.get("data") or {}).get("token")
                or ""
            )

            # Fallback: extract from cookies (WeTrack sets 'accessToken' cookie)
            if not token:
                # Check response cookies dict first (httpx parses these)
                token = (
                    response.cookies.get("accessToken")
                    or response.cookies.get("token")
                    or ""
                )

            # Also check raw Set-Cookie header as last resort
            if not token:
                set_cookie = response.headers.get("set-cookie", "")
                for part in set_cookie.split(";"):
                    part = part.strip()
                    if part.startswith("accessToken="):
                        token = part[len("accessToken="):]
                        break
                    if part.startswith("token="):
                        token = part[len("token="):]
                        break

            # Store cookie jar for session-based auth fallback
            self._cookies = dict(response.cookies)

            self._token = token
            return {"success": True, "message": "Signed in successfully", "data": data}
        else:
            error_data = {}
            try:
                error_data = response.json()
            except Exception:
                pass
            return {
                "success": False,
                "message": error_data.get(
                    "message",
                    error_data.get("error", f"Sign-in failed: HTTP {response.status_code}"),
                ),
                "status_code": response.status_code,
            }

    async def sign_out(self) -> dict:
        """Sign out and clear the stored token."""
        from .client import make_request
        result = await make_request("POST", "/api/auth/sign-out")
        self._token = ""
        return result

    async def ensure_authenticated(self) -> None:
        """
        Ensure a valid token is present before making API calls.

        Priority:
          1. Token already set (via SSO or wetrack_set_token) → use it.
          2. Email + password in .env → auto-login silently.
          3. Neither → raise a clear SSO prompt instead of a cryptic error.
        """
        if self._token:
            return

        # Fallback: try email/password if configured
        if config.EMAIL and config.PASSWORD:
            result = await self.sign_in()
            if not result.get("success"):
                raise RuntimeError(
                    f"WeTrack auto-login failed: {result.get('message')}. "
                    "Check WETRACK_EMAIL and WETRACK_PASSWORD in your .env file."
                )
            return

        # No credentials at all → guide user to SSO
        raise RuntimeError(
            "Not authenticated. "
            "Please run the 'wetrack_microsoft_sso_login' tool to sign in with "
            "your Microsoft account, or set WETRACK_EMAIL + WETRACK_PASSWORD in "
            "your .env file for email/password login."
        )


# Singleton — shared across all tool modules
auth_manager = AuthManager()
