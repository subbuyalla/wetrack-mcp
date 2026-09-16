"""
WeTrack Enterprise MCP Server — Entry Point

Exposes all WeTrack API endpoints as MCP tools for AI assistants
(Claude Desktop, Cursor, Gemini, and any MCP-compatible client).

Transport: stdio (default) or SSE/HTTP
Auth:      Bearer JWT, auto-login from .env credentials
"""

import asyncio
import sys
from pydantic import AnyHttpUrl
from mcp.server.mcpserver import MCPServer as FastMCP
from mcp.server.auth.settings import AuthSettings
from .config import config
from .auth import auth_manager
from .server_auth import OAuthTokenVerifier
from .tools import register_all_tools

# ── Configure Server-Side OAuth 2.1 Auth (RFC 9470 Protected Resource) ────────
server_auth_settings = None
server_token_verifier = None

if config.OAUTH_ENABLED:
    server_auth_settings = AuthSettings(
        issuer_url=AnyHttpUrl(config.OAUTH_ISSUER_URL),
        resource_server_url=AnyHttpUrl(config.RESOURCE_SERVER_URL),
        required_scopes=config.OAUTH_REQUIRED_SCOPES,
        validate_token_resource=False,
    )
    server_token_verifier = OAuthTokenVerifier()

# ── Create the MCP server ─────────────────────────────────────────────────────
mcp = FastMCP(
    name="WeTrack Enterprise MCP",
    instructions=(
        "You are connected to WeTrack — an enterprise project and ticket management platform. "
        "You can manage tickets (EPICs, Stories, Tasks, Bugs), projects, sprints, users, "
        "client organisations, reports, notifications, and more via 111 available tools. "
        "\n\n"
        "AUTHENTICATION RULES (follow these exactly):\n"
        "1. NEVER ask the user for a username, password, or credentials of any kind.\n"
        "2. If any tool returns 'authenticated: false' or 'action_required', "
        "you MUST immediately and automatically call 'wetrack_microsoft_sso_login' "
        "without asking the user anything first.\n"
        "3. After SSO login is complete, retry the original tool call.\n"
        "4. wetrack_microsoft_sso_login opens the browser automatically — "
        "just call it and tell the user their browser is opening for Microsoft login."
    ),
    auth=server_auth_settings,
    token_verifier=server_token_verifier,
)

# ── Register all tool modules ─────────────────────────────────────────────────
register_all_tools(mcp)


# ── Startup hook — auto-login if credentials are configured ──────────────────
@mcp.resource("wetrack://status")
async def get_server_status() -> str:
    """Returns the current WeTrack MCP server status and auth state."""
    authenticated = auth_manager.is_authenticated()
    base_url = config.BASE_URL

    status_lines = [
        "# WeTrack MCP Server Status",
        f"- Base URL: {base_url}",
        f"- Authenticated: {'✅ Yes' if authenticated else '❌ No — call wetrack_microsoft_sso_login to sign in'}",
        f"- Transport: {config.MCP_TRANSPORT}",
        "",
        "## Available Tool Modules",
        "- 🔐 Auth (7 tools)",
        "- 🔑 OAuth / SSO (3 tools)",
        "- 🎫 Tickets (13 tools)",
        "- 📁 Projects + Files (17 tools)",
        "- 🏃 Sprints (5 tools)",
        "- 👤 Users (7 tools)",
        "- 🏢 Clients + Organisations (7 tools)",
        "- 📊 Dashboard (1 tool)",
        "- 📈 Reports + Widgets (11 tools)",
        "- 🔔 Notifications (4 tools)",
        "- 🔍 Search (1 tool)",
        "- 🗂️ Master Data (17 tools)",
        "- 🧩 Metadata Fields (6 tools)",
        "- 📤 Uploads (2 tools)",
        "- ⚡ Webhooks & Cron (3 tools)",
        "",
        "**Total: 110 tools**",
    ]
    return "\n".join(status_lines)


def main():
    """
    Start the WeTrack MCP server.

    Transport is controlled by the MCP_TRANSPORT environment variable:
    - 'stdio' (default) — for Claude Desktop, Cursor, and local AI clients
    - 'sse'             — for remote/web MCP clients

    Credentials are auto-loaded from .env:
    - WETRACK_EMAIL and WETRACK_PASSWORD trigger auto-login on first tool call
    - Or set WETRACK_TOKEN directly to skip auto-login
    """
    # Pre-populate token from env if set
    if config.TOKEN:
        auth_manager.token = config.TOKEN
        print(f"[WeTrack MCP] Using pre-set token from WETRACK_TOKEN", file=sys.stderr)
    elif config.EMAIL and config.PASSWORD:
        print(
            f"[WeTrack MCP] Credentials configured — will auto-login as {config.EMAIL} on first request",
            file=sys.stderr,
        )
    else:
        print(
            "[WeTrack MCP] ⚠️  No credentials found. Set WETRACK_EMAIL + WETRACK_PASSWORD "
            "in .env, or call wetrack_sign_in manually.",
            file=sys.stderr,
        )

    print(f"[WeTrack MCP] Starting on transport: {config.MCP_TRANSPORT}", file=sys.stderr)
    print(f"[WeTrack MCP] Base URL: {config.BASE_URL}", file=sys.stderr)
    if config.OAUTH_ENABLED:
        print(f"[WeTrack MCP] 🔐 Server-side OAuth 2.1: ENABLED (RFC 9470 Protected Resource)", file=sys.stderr)
        print(f"[WeTrack MCP] 🔐 Issuer: {config.OAUTH_ISSUER_URL}", file=sys.stderr)
        print(f"[WeTrack MCP] 🔐 Metadata: {config.RESOURCE_SERVER_URL}/.well-known/oauth-protected-resource", file=sys.stderr)
    else:
        print(f"[WeTrack MCP] 🔓 Server-side OAuth 2.1: DISABLED", file=sys.stderr)

    if config.MCP_TRANSPORT == "sse":
        mcp.run(transport="sse", host=config.MCP_HOST, port=config.MCP_PORT)
    elif config.MCP_TRANSPORT == "streamable-http":
        mcp.run(transport="streamable-http", host=config.MCP_HOST, port=config.MCP_PORT)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
