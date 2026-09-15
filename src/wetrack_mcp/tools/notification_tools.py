"""Notification Tools — feed, unread count, mark read."""

import json
from typing import Optional
from ..client import make_request


def register_notification_tools(mcp):

    @mcp.tool()
    async def wetrack_list_notifications(
        status: str = "all",
        category: str = "all",
        project_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> str:
        """
        Retrieve paginated notifications for the authenticated user.

        Args:
            status: Filter by read status — 'all' (default), 'unread', or 'read'.
            category: Filter by type — 'all' (default), 'comment', or 'update'.
            project_id: Filter notifications to a specific project UUID.
            page: Page number (default: 1).
            limit: Items per page, max 100 (default: 20).
        """
        result = await make_request(
            "GET",
            "/api/notifications",
            params={
                "status": status,
                "category": category,
                "projectId": project_id,
                "page": page,
                "limit": limit,
            },
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_unread_notification_count() -> str:
        """
        Get the total number of unread notifications for the authenticated user.
        Useful for showing a badge count.
        """
        result = await make_request("GET", "/api/notifications/unread-count")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_mark_notification_read(notification_id: str) -> str:
        """
        Mark a single notification as read.

        Args:
            notification_id: Notification ID e.g. 'hist_123' or 'comm_456'.
        """
        result = await make_request(
            "PATCH", f"/api/notifications/{notification_id}/read"
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_mark_all_notifications_read() -> str:
        """
        Mark ALL notifications as read for the authenticated user at once.
        """
        result = await make_request("POST", "/api/notifications/read-all")
        return json.dumps(result, indent=2)
