"""
Microsoft OAuth Tools — start sign-in flow and handle callback.

Note: These tools return the redirect URL for you to navigate to in a browser.
The MCP server itself cannot perform browser redirects — you must open the
returned URL yourself, after which WeTrack sets a session cookie.
For MCP usage the recommended flow is:
  1. Call wetrack_get_microsoft_signin_url → get the Microsoft auth URL
  2. Open that URL in a browser → complete Microsoft login
  3. WeTrack auto-creates/logs in your account and sets a cookie
  4. Extract the JWT token from the response or cookie and call
     wetrack_set_token to store it for subsequent MCP calls.
"""

import json
from ..client import make_request
from ..auth import auth_manager


def register_oauth_tools(mcp):

    @mcp.tool()
    async def wetrack_get_microsoft_signin_url() -> str:
        """
        Get the Microsoft OAuth sign-in URL to start the login flow.

        Returns a URL that the user must open in a browser to complete
        Microsoft/Azure AD authentication. After login, WeTrack will set
        a session cookie and redirect to the configured success URL.

        Workflow:
          1. Call this tool to get the Microsoft OAuth URL.
          2. Open the URL in your browser.
          3. Complete Microsoft login.
          4. Copy the JWT token from the WeTrack response/cookie.
          5. Call wetrack_set_token with the token to use it here.

        Note: Microsoft OAuth requires browser interaction and cannot be
        automated fully through MCP. Use email/password sign-in for
        non-SSO accounts via wetrack_sign_in.
        """
        result = await make_request(
            "GET",
            "/api/auth/microsoft/sign-in",
            auto_login=False,
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_set_token(token: str) -> str:
        """
        Manually set a JWT token for all subsequent WeTrack API calls.
        Use this after completing Microsoft OAuth login in a browser to
        store your token in the MCP server session.

        Args:
            token: The JWT Bearer token string from your WeTrack session.

        After setting this, all tool calls will use Bearer <token>
        automatically. The token is stored in-memory for this session only.
        """
        auth_manager.token = token
        return json.dumps({
            "success": True,
            "message": "Token set successfully. All future requests will use this token.",
        }, indent=2)

    @mcp.tool()
    async def wetrack_get_oauth_callback_info() -> str:
        """
        Get information about the Microsoft OAuth callback endpoint.
        This endpoint is called automatically by Microsoft after login —
        it resolves the identity to a WeTrack user (auto-registering on
        first login) and issues a session.

        Returns documentation about the callback flow rather than calling
        the endpoint (which requires browser-level interaction with state params).
        """
        return json.dumps({
            "success": True,
            "data": {
                "callback_url": "GET /api/auth/microsoft/callback",
                "description": (
                    "Called automatically by Microsoft after OAuth login. "
                    "Resolves identity to a WeTrack user and issues a JWT session. "
                    "First-time login auto-creates a EMPLOYEE-role account. "
                    "Possible error codes: invalid_state, exchange_failed, "
                    "tenant_not_configured, inactive_account, org_mismatch."
                ),
                "how_to_use_oauth_with_mcp": [
                    "1. Call wetrack_get_microsoft_signin_url to get the OAuth URL.",
                    "2. Open that URL in your browser.",
                    "3. Complete Microsoft authentication.",
                    "4. After WeTrack redirects you to the success URL, copy the JWT token.",
                    "5. Call wetrack_set_token with the token to authenticate MCP calls.",
                ],
            },
        }, indent=2)
