"""
WeTrack Enterprise MCP Server — Entry Point

Exposes all WeTrack API endpoints as MCP tools for AI assistants
(Claude Desktop, Cursor, Gemini, and any MCP-compatible client).

Transport: stdio (default) or SSE/HTTP
Auth:      Bearer JWT, auto-login from .env credentials
"""

import asyncio
import sys
from mcp.server.mcpserver import MCPServer as FastMCP
from .config import config
from .auth import auth_manager
from .tools import register_all_tools

# ── Create the MCP server ─────────────────────────────────────────────────────
mcp = FastMCP(
    name="WeTrack Enterprise MCP",
    instructions=(
        "You are connected to WeTrack (VTrack) — an enterprise project management platform. "
        "You can manage tickets (EPICs, Stories, Tasks, Bugs), projects, sprints, users, "
        "client organisations, reports, notifications, and more. "
        "Authentication is handled automatically. If you see a 401 error, call "
        "wetrack_sign_in with valid credentials. "
        "Always use wetrack_get_current_user to confirm who is logged in before "
        "making changes on behalf of a user."
    ),
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
        f"- Authenticated: {'✅ Yes' if authenticated else '❌ No (call wetrack_sign_in)'}",
        f"- Transport: {config.MCP_TRANSPORT}",
        "",
        "## Available Tool Modules",
        "- 🔐 Auth (7 tools)",
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
        "",
        "**Total: ~76 tools**",
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

    if config.MCP_TRANSPORT == "sse":
        mcp.run(transport="sse", host=config.MCP_HOST, port=config.MCP_PORT)
    elif config.MCP_TRANSPORT == "streamable-http":
        mcp.run(transport="streamable-http", host=config.MCP_HOST, port=config.MCP_PORT)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
