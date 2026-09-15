"""WeTrack MCP Tools — registers all tools on the MCP server instance."""

from .auth_tools import register_auth_tools
from .ticket_tools import register_ticket_tools
from .project_tools import register_project_tools
from .sprint_tools import register_sprint_tools
from .user_tools import register_user_tools
from .client_tools import register_client_tools
from .dashboard_tools import register_dashboard_tools
from .report_tools import register_report_tools
from .notification_tools import register_notification_tools
from .search_tools import register_search_tools
from .master_tools import register_master_tools
from .metadata_tools import register_metadata_tools
from .oauth_tools import register_oauth_tools
from .upload_tools import register_upload_tools
from .webhook_tools import register_webhook_tools


def register_all_tools(mcp):
    """Register every WeTrack tool module onto the MCP server."""
    register_auth_tools(mcp)
    register_ticket_tools(mcp)
    register_project_tools(mcp)
    register_sprint_tools(mcp)
    register_user_tools(mcp)
    register_client_tools(mcp)
    register_dashboard_tools(mcp)
    register_report_tools(mcp)
    register_notification_tools(mcp)
    register_search_tools(mcp)
    register_master_tools(mcp)
    register_metadata_tools(mcp)
    register_oauth_tools(mcp)
    register_upload_tools(mcp)
    register_webhook_tools(mcp)
