"""
Ticket Tools — EPIC, STORY, TASK, BUG work items + legacy support tickets.
Covers: create, list, get, update, comments, history, attachments, watch.
"""

import json
from typing import Optional
from ..client import make_request


def register_ticket_tools(mcp):

    @mcp.tool()
    async def wetrack_list_tickets(
        project_id: Optional[str] = None,
        ticket_type: Optional[str] = None,
        sprint_id: Optional[str] = None,
        status_id: Optional[str] = None,
        priority_id: Optional[str] = None,
        search: Optional[str] = None,
        assigned_to_me: Optional[bool] = None,
        is_backlog: Optional[bool] = None,
        is_active_sprint: Optional[bool] = None,
        due_date: Optional[str] = None,
        sort_order: Optional[str] = None,
        view: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> str:
        """
        List and filter tickets (work items and support tickets).

        Args:
            project_id: Filter by project UUID. Comma-separated for multiple.
            ticket_type: Filter by type — EPIC, STORY, TASK, BUG (comma-separated).
            sprint_id: Sprint UUID. Pass 'null' or 'unassigned' for backlog.
            status_id: Status ID(s), comma-separated.
            priority_id: Priority ID(s), comma-separated.
            search: Case-insensitive search against title or summary.
            assigned_to_me: If true, only show tickets assigned to me.
            is_backlog: If true, only show backlog tickets (no sprint assigned).
            is_active_sprint: If true, only show tickets in the active sprint.
            due_date: Filter bucket — 'Overdue', 'Due Today', 'Due This Week', 'Due This Month', 'No Due Date'.
            sort_order: 'asc' or 'desc' (default: desc = newest first).
            view: Response shape — 'default' (full), 'card' (board), 'summary' (dropdown).
            page: Page number (default: 1).
            limit: Rows per page, max 100 (default: 20).
        """
        result = await make_request(
            "GET",
            "/api/tickets",
            params={
                "project_id": project_id,
                "type": ticket_type,
                "sprint_id": sprint_id,
                "statusId": status_id,
                "priorityId": priority_id,
                "search": search,
                "assignedToMe": assigned_to_me,
                "isBacklog": is_backlog,
                "isActiveSprint": is_active_sprint,
                "dueDate": due_date,
                "sortOrder": sort_order,
                "view": view,
                "page": page,
                "limit": limit,
            },
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_ticket(ticket_id: str) -> str:
        """
        Get full details of a single ticket by its ID.
        Returns different shapes for work items (EPIC/STORY/TASK/BUG) vs support tickets.

        Args:
            ticket_id: The ticket UUID or numeric ID.
        """
        result = await make_request("GET", f"/api/tickets/{ticket_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_work_item(
        ticket_type: str,
        title: str,
        summary: str,
        project_id: str,
        priority_id: int,
        status_id: Optional[int] = None,
        description: Optional[str] = None,
        assignees: Optional[list[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tags: Optional[list[str]] = None,
        sprint_id: Optional[str] = None,
        story_points: Optional[int] = None,
        bug_type: Optional[str] = None,
        parent_id: Optional[int] = None,
    ) -> str:
        """
        Create a new work item — EPIC, STORY, TASK, or BUG.

        Args:
            ticket_type: 'EPIC', 'STORY', 'TASK', or 'BUG'.
            title: Work item title (Epic Name / Story Name / Task Name / Bug Title).
            summary: Short summary of the work item.
            project_id: UUID of the project this belongs to.
            priority_id: Integer ID of the priority (get from wetrack_list_ticket_priorities).
            status_id: Status ID (defaults to 'To Do' if omitted).
            description: Optional rich text description (HTML supported). Required for BUG.
            assignees: List of user UUIDs to assign. First becomes primary assignee.
            start_date: ISO datetime string e.g. '2026-09-01T00:00:00Z'.
            end_date: ISO datetime string. Must be after start_date.
            tags: List of string tags.
            sprint_id: UUID of the sprint to assign this to (optional).
            story_points: Integer story points. Required for STORY, optional for TASK/BUG.
            bug_type: Bug category string. Required for BUG type only.
            parent_id: Integer ID of parent EPIC (for STORY/TASK/BUG only).
        """
        payload = {
            "type": ticket_type.upper(),
            "title": title,
            "summary": summary,
            "projectId": project_id,
            "priorityId": priority_id,
        }
        if status_id is not None:
            payload["statusId"] = status_id
        if description:
            payload["description"] = description
        if assignees:
            payload["assignees"] = assignees
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        if tags:
            payload["tags"] = tags
        if sprint_id:
            payload["sprintId"] = sprint_id
        if story_points is not None:
            payload["storyPoints"] = story_points
        if bug_type:
            payload["bugType"] = bug_type
        if parent_id is not None:
            payload["parentId"] = parent_id

        result = await make_request("POST", "/api/tickets", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_support_ticket(
        title: str,
        request_status_id: int,
        request_priority_id: int,
        organisation_id: str,
        project_id: str,
        description: Optional[str] = None,
        request_type_id: Optional[int] = None,
        category_id: Optional[int] = None,
        assigned_to: Optional[int] = None,
        reporting_to: Optional[int] = None,
        due_date: Optional[str] = None,
        start_date: Optional[str] = None,
        estimate: Optional[float] = None,
    ) -> str:
        """
        Create a legacy support ticket (not an EPIC/STORY/TASK/BUG work item).

        Args:
            title: Ticket title e.g. 'Login issue on portal'.
            request_status_id: Integer status ID.
            request_priority_id: Integer priority ID.
            organisation_id: UUID of the client organisation.
            project_id: UUID of the project.
            description: Rich HTML description (up to 2MB).
            request_type_id: Optional ticket type ID.
            category_id: Optional category ID.
            assigned_to: Optional user integer ID to assign.
            reporting_to: Optional reporter user integer ID.
            due_date: ISO datetime for due date.
            start_date: ISO datetime for start.
            estimate: Estimated hours (float).
        """
        payload = {
            "title": title,
            "request_status_id": request_status_id,
            "request_priority_id": request_priority_id,
            "organisation_id": organisation_id,
            "project_id": project_id,
        }
        if description:
            payload["description"] = description
        if request_type_id:
            payload["request_type_id"] = request_type_id
        if category_id:
            payload["category_id"] = category_id
        if assigned_to:
            payload["assigned_to"] = assigned_to
        if reporting_to:
            payload["reporting_to"] = reporting_to
        if due_date:
            payload["due_date"] = due_date
        if start_date:
            payload["start_date"] = start_date
        if estimate is not None:
            payload["estimate"] = estimate

        result = await make_request("POST", "/api/tickets/create", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_ticket(
        ticket_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        request_status_id: Optional[int] = None,
        request_priority_id: Optional[int] = None,
        assignees: Optional[list[str]] = None,
        summary: Optional[str] = None,
        story_points: Optional[int] = None,
        bug_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        end_date: Optional[str] = None,
        parent_id: Optional[int] = None,
        sprint_id: Optional[str] = None,
    ) -> str:
        """
        Update a ticket's fields. Only fields you provide are changed.

        Args:
            ticket_id: UUID of the ticket to update.
            title: New title.
            description: New rich HTML description.
            request_status_id: New status ID.
            request_priority_id: New priority ID.
            assignees: New list of assignee user UUIDs (replaces all existing assignees).
            summary: New short summary.
            story_points: New story points (positive integer).
            bug_type: New bug category.
            tags: New tag list (replaces existing).
            end_date: New due date (ISO datetime).
            parent_id: Reassign to a different parent EPIC.
            sprint_id: Move to a different sprint UUID.
        """
        payload = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if request_status_id is not None:
            payload["request_status_id"] = request_status_id
        if request_priority_id is not None:
            payload["request_priority_id"] = request_priority_id
        if assignees is not None:
            payload["assignees"] = assignees
        if summary is not None:
            payload["summary"] = summary
        if story_points is not None:
            payload["storyPoints"] = story_points
        if bug_type is not None:
            payload["bugType"] = bug_type
        if tags is not None:
            payload["tags"] = tags
        if end_date is not None:
            payload["endDate"] = end_date
        if parent_id is not None:
            payload["parentId"] = parent_id
        if sprint_id is not None:
            payload["sprintId"] = sprint_id

        result = await make_request("PUT", f"/api/tickets/{ticket_id}", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_ticket_comments(ticket_id: str) -> str:
        """
        Get all comments on a ticket, in chronological order.

        Args:
            ticket_id: The ticket UUID.
        """
        result = await make_request("GET", f"/api/tickets/{ticket_id}/comments")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_add_ticket_comment(ticket_id: str, comment: str) -> str:
        """
        Add a comment to a ticket.

        Args:
            ticket_id: The ticket UUID.
            comment: Comment text e.g. 'Investigating the issue now.'
        """
        result = await make_request(
            "POST",
            f"/api/tickets/{ticket_id}/comments",
            json={"comment": comment},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_ticket_history(ticket_id: str) -> str:
        """
        Get the full audit history/changelog for a ticket.
        Shows every field change with who made it and when.

        Args:
            ticket_id: The ticket UUID.
        """
        result = await make_request("GET", f"/api/tickets/{ticket_id}/history")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_ticket_attachments(ticket_id: str) -> str:
        """
        List all file attachments on a ticket.

        Args:
            ticket_id: The ticket UUID.
        """
        result = await make_request("GET", f"/api/tickets/{ticket_id}/attachments")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_add_ticket_attachment(
        ticket_id: str,
        url: str,
        file_name: str,
        file_size: float,
        file_type: Optional[str] = None,
    ) -> str:
        """
        Add a file attachment to a ticket (the file must already be uploaded to S3).
        Use wetrack_get_upload_presign_url to upload to S3 first, then call this.

        Args:
            ticket_id: The ticket UUID.
            url: S3 URL of the uploaded file.
            file_name: Original file name e.g. 'screenshot.png'.
            file_size: File size in bytes.
            file_type: MIME type e.g. 'image/png'.
        """
        payload = {"url": url, "fileName": file_name, "fileSize": file_size}
        if file_type:
            payload["fileType"] = file_type
        result = await make_request(
            "POST", f"/api/tickets/{ticket_id}/attachments", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_delete_ticket_attachment(
        ticket_id: str, attachment_id: str
    ) -> str:
        """
        Delete an attachment from a ticket.

        Args:
            ticket_id: The ticket UUID.
            attachment_id: The attachment UUID to delete.
        """
        result = await make_request(
            "DELETE", f"/api/tickets/{ticket_id}/attachments/{attachment_id}"
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_ticket_watchers(ticket_id: str) -> str:
        """
        Get the watch/follow status and list of watchers for a ticket.

        Args:
            ticket_id: The ticket UUID.
        """
        result = await make_request("GET", f"/api/tickets/{ticket_id}/watch")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_toggle_ticket_watch(ticket_id: str) -> str:
        """
        Toggle your watch/follow status on a ticket.
        If you're not watching, this starts watching. If you are, it stops.

        Args:
            ticket_id: The ticket UUID.
        """
        result = await make_request("POST", f"/api/tickets/{ticket_id}/watch")
        return json.dumps(result, indent=2)
