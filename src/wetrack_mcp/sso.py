"""
Shared SSO state and local callback server.
Imported by both client.py (auto-trigger) and oauth_tools.py (manual trigger).
"""

import json
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# ── Shared state ──────────────────────────────────────────────────────────────
sso_state: dict = {"token": None, "done": False, "port": None}


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def make_handler(state: dict, set_token_fn):
    HELPER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>WeTrack MCP — Complete Login</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, -apple-system, sans-serif; background: #0f172a;
          color: #e2e8f0; min-height: 100vh; display: flex; align-items: center;
          justify-content: center; padding: 24px; }}
  .card {{ background: #1e293b; border-radius: 16px; padding: 40px;
           max-width: 540px; width: 100%; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }}
  .logo {{ font-size: 28px; font-weight: 800; color: #6366f1; margin-bottom: 8px; }}
  .subtitle {{ color: #94a3b8; margin-bottom: 32px; font-size: 15px; }}
  .steps {{ background: #0f172a; border-radius: 10px; padding: 20px;
            margin-bottom: 24px; border-left: 3px solid #6366f1; }}
  .steps ol {{ padding-left: 20px; }}
  .steps li {{ margin-bottom: 8px; color: #cbd5e1; font-size: 14px; line-height: 1.6; }}
  .steps li strong {{ color: #e2e8f0; }}
  label {{ display: block; font-size: 13px; color: #94a3b8; margin-bottom: 8px; }}
  input {{ width: 100%; padding: 12px 16px; background: #0f172a; border: 1px solid #334155;
           border-radius: 8px; color: #e2e8f0; font-size: 13px; font-family: monospace;
           margin-bottom: 16px; outline: none; }}
  input:focus {{ border-color: #6366f1; }}
  button {{ width: 100%; padding: 14px; background: #6366f1; color: #fff; border: none;
             border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;
             transition: background 0.2s; }}
  button:hover {{ background: #4f46e5; }}
  .ok {{ color: #22c55e; font-weight: 600; text-align: center; padding: 16px;
          background: #052e16; border-radius: 8px; }}
  .err {{ color: #f87171; font-weight: 600; text-align: center; padding: 12px;
           background: #2d1515; border-radius: 8px; }}
</style>
</head>
<body>
<div class="card">
  <div class="logo">WeTrack MCP</div>
  <div class="subtitle">Complete your Microsoft SSO login</div>
  <div class="steps">
    <ol>
      <li>Complete Microsoft sign-in in the other tab.</li>
      <li>Press <strong>F12</strong> &rarr; Application &rarr; Cookies &rarr; <strong>vtrack-internal.vercel.app</strong></li>
      <li>Copy the value of the <strong>accessToken</strong> cookie.</li>
      <li>Paste it below and click <strong>Complete Login</strong>.</li>
    </ol>
  </div>
  <label>accessToken cookie value</label>
  <input id="tok" type="text" placeholder="eyJhbGciOiJIUzI1NiIs..." />
  <button onclick="submit()">Complete Login</button>
  <p id="msg"></p>
</div>
<script>
function submit() {{
  var t = document.getElementById('tok').value.trim();
  if (!t) {{ document.getElementById('msg').innerHTML = '<div class="err">Please paste your accessToken first.</div>'; return; }}
  fetch('/receive?token=' + encodeURIComponent(t))
    .then(r => r.json())
    .then(d => {{
      if (d.success) {{
        document.getElementById('msg').innerHTML = '<div class="ok">&#10003; Login complete! Go back to Claude and retry your request.</div>';
      }} else {{
        document.getElementById('msg').innerHTML = '<div class="err">Error: ' + d.message + '</div>';
      }}
    }});
}}
</script>
</body>
</html>"""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/receive":
                params = parse_qs(parsed.query)
                token = params.get("token", [None])[0]
                if token:
                    state["token"] = token
                    state["done"] = True
                    set_token_fn(token)
                    self._respond(200, json.dumps({"success": True}), "application/json")
                else:
                    self._respond(400, json.dumps({"success": False, "message": "No token"}), "application/json")
            else:
                self._respond(200, HELPER_HTML.format(), "text/html")

        def _respond(self, code, body, ct):
            self.send_response(code)
            self.send_header("Content-Type", ct)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body.encode())

    return Handler


def run_local_server(port: int, state: dict, set_token_fn, timeout: int = 300):
    server = HTTPServer(("127.0.0.1", port), make_handler(state, set_token_fn))
    server.timeout = 5
    elapsed = 0
    while not state["done"] and elapsed < timeout:
        server.handle_request()
        elapsed += 5
    server.server_close()


def start_sso_flow(ms_url: str, set_token_fn) -> tuple[int, threading.Thread]:
    """Start the local callback server and open the browser. Returns (port, thread)."""
    sso_state["token"] = None
    sso_state["done"] = False

    port = find_free_port()
    sso_state["port"] = port

    t = threading.Thread(
        target=run_local_server,
        args=(port, sso_state, set_token_fn, 300),
        daemon=True,
    )
    t.start()
    webbrowser.open(ms_url)
    return port, t
