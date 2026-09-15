"""
Report Tools — unified reports dashboard, My Work, My Sprint,
report catalog, and personal widget management.
"""

import json
from typing import Optional
from ..client import make_request


def register_report_tools(mcp):

    @mcp.tool()
    async def wetrack_get_reports(
        project_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        status_id: Optional[str] = None,
        priority_id: Optional[str] = None,
        user_id: Optional[str] = None,
        burndown_range: Optional[str] = None,
        burndown_from: Optional[str] = None,
        burndown_to: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> str:
        """
        Unified Reports Dashboard — scoped dynamically for Admin/Manager/Employee.
        Includes stat cards, status/priority distributions, project progress,
        sprint burndown, and summary table.

        Args:
            project_id: Filter by project UUID.
            sprint_id: Filter by sprint UUID.
            status_id: Filter by ticket status ID.
            priority_id: Filter by ticket priority ID.
            user_id: Scope to tickets assigned to this user UUID.
            burndown_range: Burndown scope — 'this_month', 'this_week', 'last_30_days', 'custom'.
            burndown_from: Start date for custom burndown range (YYYY-MM-DD).
            burndown_to: End date for custom burndown range (YYYY-MM-DD).
            page: Page number (default: 1).
            limit: Rows per page (default: 10).
        """
        result = await make_request(
            "GET",
            "/api/reports",
            params={
                "project_id": project_id,
                "sprint_id": sprint_id,
                "status_id": status_id,
                "priority_id": priority_id,
                "user_id": user_id,
                "burndown_range": burndown_range,
                "burndown_from": burndown_from,
                "burndown_to": burndown_to,
                "page": page,
                "limit": limit,
            },
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_reports_catalog() -> str:
        """
        List every report available to the current user's role.
        Shows dataSource type ('existing', 'generic', 'custom') and default
        metric/dimension/chartType to use when creating a widget.
        """
        result = await make_request("GET", "/api/reports/catalog")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_my_work_report(
        project_id: Optional[str] = None,
        status_id: Optional[str] = None,
        priority_id: Optional[str] = None,
        date_range: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> str:
        """
        Current user's My Work report — stat cards, status/priority distributions,
        and a ticket list scoped to what's assigned to me.

        Args:
            project_id: Filter by project UUID.
            status_id: Filter by status ID.
            priority_id: Filter by priority ID.
            date_range: 'this_week', 'this_month', 'this_sprint', or 'custom'.
            from_date: Start of custom date range (YYYY-MM-DD).
            to_date: End of custom date range (YYYY-MM-DD).
            page: Page number.
            limit: Items per page.
        """
        result = await make_request(
            "GET",
            "/api/reports/my/work",
            params={
                "project_id": project_id,
                "status_id": status_id,
                "priority_id": priority_id,
                "range": date_range,
                "from": from_date,
                "to": to_date,
                "page": page,
                "limit": limit,
            },
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_my_sprint_report(
        sprint_id: Optional[str] = None,
        status_id: Optional[str] = None,
        priority_id: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> str:
        """
        Current user's My Sprint report — progress, burndown, distributions,
        and ticket list for the sprint the current user is part of.

        Args:
            sprint_id: Sprint UUID (defaults to the user's current active sprint).
            status_id: Filter by status ID.
            priority_id: Filter by priority ID.
            page: Page number.
            limit: Items per page.
        """
        result = await make_request(
            "GET",
            "/api/reports/my/sprint",
            params={
                "sprint_id": sprint_id,
                "status_id": status_id,
                "priority_id": priority_id,
                "page": page,
                "limit": limit,
            },
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_list_widgets() -> str:
        """
        List the current user's report widgets in display order.
        Each widget has an id, metric, dimension, chartType, isVisible, and orderIndex.
        """
        result = await make_request("GET", "/api/reports/my/widgets")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_widget(
        title: str,
        metric: str,
        dimension: str,
        chart_type: str,
        catalog_report_id: Optional[str] = None,
    ) -> str:
        """
        Add a report widget to the current user's dashboard.

        Args:
            title: Display title shown on the widget card (non-empty).
            metric: What to measure — one of:
                    'COUNT_OF_TICKETS', 'COUNT_CREATED_VS_COMPLETED', 'AVG_CYCLE_TIME',
                    'AVG_RESPONSE_TIME', 'AVG_TICKET_AGE', 'SUM_STORY_POINTS',
                    'SUM_TIME_SPENT', 'COUNT_BLOCKED'.
            dimension: Group-by dimension — one of:
                       'PROJECT', 'SPRINT', 'SPRINT_STATUS', 'ASSIGNEE', 'REPORTER',
                       'STATUS', 'STATUS_CATEGORY', 'PRIORITY', 'TYPE', 'PARENT',
                       'DUE_DATE_BUCKET', 'CREATED_DATE', 'RESOLVED_DATE', 'BLOCKED', 'BUG_TYPE'.
            chart_type: How to render — 'BAR', 'LINE', 'PIE', 'DONUT', 'TABLE', or 'AREA'.
            catalog_report_id: Optional id from wetrack_get_reports_catalog
                               to link to a catalog entry (e.g. 'status_breakdown').
        """
        payload: dict = {
            "title": title,
            "metric": metric,
            "dimension": dimension,
            "chartType": chart_type,
        }
        if catalog_report_id:
            payload["catalogReportId"] = catalog_report_id

        result = await make_request("POST", "/api/reports/my/widgets", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_widget(
        widget_id: str,
        title: Optional[str] = None,
        metric: Optional[str] = None,
        dimension: Optional[str] = None,
        chart_type: Optional[str] = None,
        is_visible: Optional[bool] = None,
    ) -> str:
        """
        Update a report widget. At least one field must be provided.

        Args:
            widget_id: Widget ID from wetrack_list_widgets.
            title: New display title (non-empty if provided).
            metric: New metric — see wetrack_create_widget for valid values.
            dimension: New dimension — see wetrack_create_widget for valid values.
            chart_type: Switch chart type — 'BAR', 'LINE', 'PIE', 'DONUT', 'TABLE', 'AREA'.
            is_visible: Show/hide the widget (True = show, False = hide).
        """
        payload = {}
        if title is not None:
            payload["title"] = title
        if metric is not None:
            payload["metric"] = metric
        if dimension is not None:
            payload["dimension"] = dimension
        if chart_type is not None:
            payload["chartType"] = chart_type
        if is_visible is not None:
            payload["isVisible"] = is_visible

        result = await make_request(
            "PUT", f"/api/reports/my/widgets/{widget_id}", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_delete_widget(widget_id: str) -> str:
        """
        Delete a report widget from the current user's dashboard.

        Args:
            widget_id: Widget ID from wetrack_list_widgets.
        """
        result = await make_request(
            "DELETE", f"/api/reports/my/widgets/{widget_id}"
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_widget_data(widget_id: str) -> str:
        """
        Run a widget's metric+dimension query and return chart-ready data.
        Returns label/value pairs (one per group, up to 50 groups).

        Args:
            widget_id: Widget ID from wetrack_list_widgets or wetrack_create_widget.
        """
        result = await make_request(
            "GET", f"/api/reports/my/widgets/{widget_id}/data"
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_reorder_widgets(ordered_ids: list[str]) -> str:
        """
        Persist the display order of the current user's report widgets.

        Args:
            ordered_ids: ALL widget IDs in the desired top-to-bottom order
                         (not just the one that moved). Get current IDs from
                         wetrack_list_widgets first.

        Example: ["widget-id-1", "widget-id-2", "widget-id-3"]
        """
        result = await make_request(
            "PATCH",
            "/api/reports/my/widgets/reorder",
            json={"orderedIds": ordered_ids},
        )
        return json.dumps(result, indent=2)
