"""
Microsoft OAuth Tools — automated SSO flow with local callback server.

The primary SSO entry point is wetrack_microsoft_sso_login.
The SSO flow is also triggered automatically by any tool that requires auth
when the user is not yet logged in (via client.py → sso.py).
"""

import json
from ..client import make_request
from ..auth import auth_manager
from ..sso import start_sso_flow, sso_state


def register_oauth_tools(mcp):

    @mcp.tool()
    async def wetrack_microsoft_sso_login() -> str:
        """
        Start an automated Microsoft SSO login for WeTrack.

        This tool:
          1. Fetches the Microsoft OAuth URL from WeTrack production.
          2. Automatically opens your default browser to the Microsoft login page.
          3. Starts a local helper page at http://127.0.0.1:PORT/ to capture your token.
          4. Once you paste the accessToken cookie value into the helper page and
             click Submit, the token is stored in this MCP session automatically.

        After this tool completes, all subsequent WeTrack tool calls will use
        your personal Microsoft identity (not the shared admin account).

        NOTE: This is also triggered automatically by any tool when not authenticated.
        """
        result = await make_request("GET", "/api/auth/microsoft/sign-in", auto_login=False)
        if not result.get("success") or not result.get("url"):
            return json.dumps({
                "success": False,
                "message": "Microsoft SSO is not configured on this WeTrack instance.",
                "details": result,
            }, indent=2)

        ms_url = result["url"]
        port, _ = start_sso_flow(ms_url, lambda t: setattr(auth_manager, "token", t))

        return json.dumps({
            "success": True,
            "message": (
                f"🔐 Browser opened for Microsoft login. "
                f"After signing in, open the helper page at http://127.0.0.1:{port}/ "
                "to paste your accessToken cookie and complete authentication."
            ),
            "steps": [
                "1. Complete Microsoft login in the browser tab that just opened.",
                "2. Press F12 → Application → Cookies → vtrack-internal.vercel.app",
                "3. Copy the value of the 'accessToken' cookie.",
                f"4. Open http://127.0.0.1:{port}/ in your browser.",
                "5. Paste the token in the helper page and click Complete Login.",
                "6. Come back to Claude — you are now authenticated!",
            ],
            "helper_url": f"http://127.0.0.1:{port}/",
        }, indent=2)

    @mcp.tool()
    async def wetrack_set_token(token: str) -> str:
        """
        Manually set a JWT token for all subsequent WeTrack API calls.

        Args:
            token: The JWT Bearer token string from your WeTrack session.

        After setting this, all tool calls will use Bearer <token> automatically.
        The token is stored in-memory for this session only.
        """
        auth_manager.token = token
        return json.dumps({
            "success": True,
            "message": "Token set successfully. All future requests will use this token.",
        }, indent=2)

    @mcp.tool()
    async def wetrack_check_sso_status() -> str:
        """
        Check whether the Microsoft SSO login has been completed.
        Returns the authenticated user profile if the token was captured successfully.
        """
        if sso_state.get("done") and auth_manager.token:
            user = await make_request("GET", "/api/users/current-user")
            return json.dumps({
                "success": True,
                "sso_complete": True,
                "message": "Microsoft SSO authentication successful!",
                "user": user.get("data", user),
            }, indent=2)
        elif sso_state.get("port"):
            return json.dumps({
                "success": True,
                "sso_complete": False,
                "message": "SSO login is in progress.",
                "helper_url": f"http://127.0.0.1:{sso_state['port']}/",
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "sso_complete": False,
                "message": "No SSO login in progress. Call wetrack_microsoft_sso_login to start.",
            }, indent=2)

    @mcp.tool()
    async def wetrack_get_oauth_callback_info() -> str:
        """Get information about the Microsoft OAuth callback endpoint and SSO flow."""
        return json.dumps({
            "success": True,
            "data": {
                "automated_flow": "Any tool automatically triggers SSO when not authenticated.",
                "callback_url": "GET /api/auth/microsoft/callback",
                "how_to_use_automated_sso": [
                    "1. Just call any WeTrack tool — SSO starts automatically if not logged in.",
                    "2. Or explicitly call wetrack_microsoft_sso_login.",
                    "3. Complete Microsoft login in the browser that opens.",
                    "4. Paste your accessToken cookie in the helper page.",
                    "5. Done — retry your original request.",
                ],
            },
        }, indent=2)
