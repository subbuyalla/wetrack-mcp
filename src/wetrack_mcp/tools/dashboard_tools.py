"""Dashboard Tools — aggregated KPIs, team workload, burndown, and health."""

import json
from typing import Optional
from ..client import make_request


def register_dashboard_tools(mcp):

    @mcp.tool()
    async def wetrack_get_dashboard(
        project_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
    ) -> str:
        """
        Get the aggregated dashboard — KPIs, Team Workload, Status Donut,
        Project Health, Pending Tickets, and Sprint Burndown.

        Args:
            project_id: Scope dashboard to a specific project UUID.
            sprint_id: Specify a sprint UUID for the burndown chart.
        """
        result = await make_request(
            "GET",
            "/api/dashboard",
            params={"projectId": project_id, "sprintId": sprint_id},
        )
        return json.dumps(result, indent=2)
