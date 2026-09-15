"""Sprint Tools — create, list, get, update, and delete sprints."""

import json
from typing import Optional
from ..client import make_request


def register_sprint_tools(mcp):

    @mcp.tool()
    async def wetrack_list_sprints(
        project_id: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        include_completed: Optional[bool] = None,
        page: int = 1,
        limit: int = 10,
    ) -> str:
        """
        List sprints across all projects or scoped to one project.

        Args:
            project_id: Filter to a single project's sprints (UUID).
            search: Case-insensitive substring match against sprint name.
            status: Comma-separated sprint statuses — 'PLANNED', 'IN_PROGRESS', 'COMPLETED'.
            include_completed: Pass False to exclude completed sprints.
            page: Page number (default: 1).
            limit: Items per page (default: 10).
        """
        result = await make_request(
            "GET",
            "/api/sprints",
            params={
                "projectId": project_id,
                "search": search,
                "status": status,
                "includeCompleted": include_completed,
                "page": page,
                "limit": limit,
            },
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_sprint(sprint_id: str) -> str:
        """
        Get full details of a single sprint.

        Args:
            sprint_id: The sprint UUID.
        """
        result = await make_request("GET", f"/api/sprints/{sprint_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_sprint(
        project_id: str,
        name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        goal: Optional[str] = None,
        status: str = "PLANNED",
    ) -> str:
        """
        Create a sprint manually for a project.

        Args:
            project_id: UUID of the project this sprint belongs to.
            name: Sprint name e.g. 'Sprint 3'.
            start_date: Start date 'YYYY-MM-DD'.
            end_date: End date 'YYYY-MM-DD'.
            goal: Sprint goal description e.g. 'Complete user auth module'.
            status: Initial status — 'PLANNED' (default), 'IN_PROGRESS', or 'COMPLETED'.
        """
        payload: dict = {"projectId": project_id, "status": status}
        if name:
            payload["name"] = name
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        if goal:
            payload["goal"] = goal

        result = await make_request("POST", "/api/sprints", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_sprint(
        sprint_id: str,
        name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        goal: Optional[str] = None,
        status: Optional[str] = None,
        move_to: Optional[str] = None,
    ) -> str:
        """
        Update sprint details, status, or goal.

        Args:
            sprint_id: The sprint UUID.
            name: New sprint name.
            start_date: New start date 'YYYY-MM-DD'.
            end_date: New end date 'YYYY-MM-DD'.
            goal: New sprint goal text.
            status: New status — 'PLANNED', 'IN_PROGRESS', or 'COMPLETED'.
            move_to: Where to move unfinished tickets when completing a sprint.
                     Use 'BACKLOG' or a target sprint UUID.
        """
        payload = {}
        if name is not None:
            payload["name"] = name
        if start_date is not None:
            payload["startDate"] = start_date
        if end_date is not None:
            payload["endDate"] = end_date
        if goal is not None:
            payload["goal"] = goal
        if status is not None:
            payload["status"] = status
        if move_to is not None:
            payload["moveTo"] = move_to

        result = await make_request(
            "PATCH", f"/api/sprints/{sprint_id}", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_delete_sprint(sprint_id: str) -> str:
        """
        Delete a sprint and unassign all linked tickets back to backlog.

        Args:
            sprint_id: The sprint UUID to delete.
        """
        result = await make_request("DELETE", f"/api/sprints/{sprint_id}")
        return json.dumps(result, indent=2)
