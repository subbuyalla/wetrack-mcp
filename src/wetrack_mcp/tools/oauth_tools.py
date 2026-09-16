"""
Microsoft OAuth Tools — automated SSO flow with local callback server.

Flow:
  1. Call wetrack_microsoft_sso_login
     → Starts a local HTTP server on a free port
     → Opens your default browser to the Microsoft login page automatically
     → Serves a helper page at http://localhost:PORT/ to capture the token
  2. Complete Microsoft login in the browser
  3. WeTrack sets your accessToken cookie
  4. Visit http://localhost:PORT/ (shown in the tool response) — paste the token
     in the helper page and click Submit
  5. The local server captures the token, stores it in the MCP session, and shuts down
  6. All future WeTrack tool calls use your personal Microsoft SSO identity
"""

import json
import asyncio
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from ..client import make_request
from ..auth import auth_manager


# ── Shared state between the local server thread and the async tool ───────────
_sso_state: dict = {"token": None, "done": False, "port": None}


def _find_free_port() -> int:
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _make_handler(state: dict):
    """Create an HTTP request handler that captures the WeTrack token."""

    HELPER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>WeTrack MCP — Complete Login</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 520px; margin: 60px auto;
          padding: 24px; background: #f8fafc; color: #1e293b; }}
  h2 {{ color: #4f46e5; }}
  input {{ width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px;
           font-size: 13px; margin: 10px 0; box-sizing: border-box; }}
  button {{ background: #4f46e5; color: #fff; border: none; padding: 10px 24px;
             border-radius: 6px; cursor: pointer; font-size: 15px; }}
  button:hover {{ background: #4338ca; }}
  .ok {{ color: #16a34a; font-weight: bold; }}
  .steps {{ background: #e0e7ff; border-radius: 8px; padding: 16px; margin: 16px 0; }}
  .steps ol {{ margin: 0; padding-left: 20px; }}
</style>
</head>
<body>
<h2>WeTrack MCP — Complete Microsoft Login</h2>
<div class="steps">
  <strong>Steps:</strong>
  <ol>
    <li>Complete Microsoft sign-in in the other tab (if not done yet).</li>
    <li>Press <strong>F12</strong> → Application → Cookies → <em>vtrack-internal.vercel.app</em></li>
    <li>Copy the value of the <strong>accessToken</strong> cookie.</li>
    <li>Paste it below and click <strong>Submit Token</strong>.</li>
  </ol>
</div>
<input id="tok" type="text" placeholder="Paste your accessToken cookie value here" />
<br>
<button onclick="submit()">Submit Token</button>
<p id="msg"></p>
<script>
function submit() {{
  var t = document.getElementById('tok').value.trim();
  if (!t) {{ document.getElementById('msg').innerText = 'Please paste your token first.'; return; }}
  fetch('/receive?token=' + encodeURIComponent(t))
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (data.success) {{
        document.getElementById('msg').innerHTML = '<span class="ok">Token saved! You can now close this tab and go back to Claude.</span>';
      }} else {{
        document.getElementById('msg').innerText = 'Error: ' + data.message;
      }}
    }});
}}
</script>
</body>
</html>"""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # Suppress default HTTP logs

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/receive":
                params = parse_qs(parsed.query)
                token = params.get("token", [None])[0]
                if token:
                    state["token"] = token
                    state["done"] = True
                    auth_manager.token = token
                    self._respond(200, json.dumps({"success": True, "message": "Token stored. You may close this tab."}), "application/json")
                else:
                    self._respond(400, json.dumps({"success": False, "message": "No token provided."}), "application/json")
            else:
                # Serve the helper HTML page
                self._respond(200, HELPER_HTML.format(), "text/html")

        def _respond(self, code, body, content_type):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body.encode())

    return Handler


def _run_local_server(port: int, state: dict, timeout: int = 300):
    """Start local HTTP server and shut it down after token is received or timeout."""
    server = HTTPServer(("127.0.0.1", port), _make_handler(state))
    server.timeout = 5  # poll every 5 seconds for done/timeout
    elapsed = 0
    while not state["done"] and elapsed < timeout:
        server.handle_request()
        elapsed += 5
    server.server_close()


def register_oauth_tools(mcp):

    @mcp.tool()
    async def wetrack_microsoft_sso_login() -> str:
        """
        Start an automated Microsoft SSO login for WeTrack.

        This tool:
          1. Fetches the Microsoft OAuth URL from WeTrack.
          2. Automatically opens your default browser to the Microsoft login page.
          3. Starts a local helper page at http://localhost:PORT/ to capture your token.
          4. Once you paste the accessToken cookie value into the helper page and
             click Submit, the token is stored in this MCP session automatically.

        After this tool completes, all subsequent WeTrack tool calls will use
        your personal Microsoft identity (not the shared admin account).

        No further tool calls are needed — just complete the login in the browser,
        copy the accessToken cookie, paste it in the helper page, and you are done!
        """
        # Reset shared state
        _sso_state["token"] = None
        _sso_state["done"] = False

        # 1. Get Microsoft OAuth URL from WeTrack
        result = await make_request("GET", "/api/auth/microsoft/sign-in", auto_login=False)
        if not result.get("success") or not result.get("url"):
            return json.dumps({
                "success": False,
                "message": "Microsoft SSO is not configured on this WeTrack instance.",
                "details": result,
            }, indent=2)

        ms_url = result["url"]

        # 2. Find a free port and start local helper server in background thread
        port = _find_free_port()
        _sso_state["port"] = port
        server_thread = threading.Thread(
            target=_run_local_server,
            args=(port, _sso_state, 300),
            daemon=True,
        )
        server_thread.start()

        # 3. Open browser automatically
        webbrowser.open(ms_url)

        return json.dumps({
            "success": True,
            "message": (
                "Browser opened for Microsoft login. "
                f"After signing in, open the helper page at http://127.0.0.1:{port}/ "
                "to paste your accessToken cookie and complete authentication automatically."
            ),
            "steps": [
                "1. Complete Microsoft login in the browser tab that just opened.",
                "2. Press F12 → Application → Cookies → vtrack-internal.vercel.app",
                "3. Copy the value of the 'accessToken' cookie.",
                f"4. Open http://127.0.0.1:{port}/ in your browser.",
                "5. Paste the token in the helper page and click Submit.",
                "6. Come back to Claude — you are authenticated with your personal Microsoft identity!",
            ],
            "helper_url": f"http://127.0.0.1:{port}/",
            "microsoft_login_url": ms_url,
        }, indent=2)

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
    async def wetrack_check_sso_status() -> str:
        """
        Check whether the Microsoft SSO login initiated by wetrack_microsoft_sso_login
        has been completed. Returns the authenticated user profile if the token
        was captured successfully via the local helper page.
        """
        if _sso_state.get("done") and auth_manager.token:
            # Verify the token works
            user = await make_request("GET", "/api/users/current-user")
            return json.dumps({
                "success": True,
                "sso_complete": True,
                "message": "Microsoft SSO authentication successful!",
                "user": user.get("data", user),
            }, indent=2)
        elif _sso_state.get("port"):
            return json.dumps({
                "success": True,
                "sso_complete": False,
                "message": "SSO login is in progress. Complete the login in your browser, then paste the token at the helper page.",
                "helper_url": f"http://127.0.0.1:{_sso_state['port']}/",
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "sso_complete": False,
                "message": "No SSO login in progress. Call wetrack_microsoft_sso_login to start.",
            }, indent=2)

    @mcp.tool()
    async def wetrack_get_oauth_callback_info() -> str:
        """
        Get information about the Microsoft OAuth callback endpoint and the
        automated SSO flow implemented in this MCP server.
        """
        return json.dumps({
            "success": True,
            "data": {
                "automated_flow": "Use wetrack_microsoft_sso_login for a one-command SSO experience.",
                "callback_url": "GET /api/auth/microsoft/callback",
                "description": (
                    "Called automatically by Microsoft after OAuth login. "
                    "Resolves identity to a WeTrack user and issues a JWT session. "
                    "First-time login auto-creates a EMPLOYEE-role account."
                ),
                "how_to_use_automated_sso": [
                    "1. Call wetrack_microsoft_sso_login.",
                    "2. Browser opens automatically to Microsoft login.",
                    "3. Complete Microsoft authentication.",
                    "4. Open the helper page URL shown in the response.",
                    "5. Paste your accessToken cookie value and click Submit.",
                    "6. Call wetrack_check_sso_status to confirm authentication.",
                ],
            },
        }, indent=2)

