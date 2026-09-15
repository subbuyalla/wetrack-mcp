"""
Master Data Tools — ticket statuses, priorities, categories, types,
products, and timezone reference data.
"""

import json
from typing import Optional
from ..client import make_request


def register_master_tools(mcp):

    # ─── Ticket Statuses ────────────────────────────────────────────────────────

    @mcp.tool()
    async def wetrack_list_ticket_statuses(
        resource: Optional[str] = None,
        include_inactive: bool = False,
    ) -> str:
        """
        Get the list of ticket statuses.

        Args:
            resource: Filter by resource — 'SPRINT', 'TASK', or 'PROJECT'.
                      Omit to return all statuses.
            include_inactive: Include soft-deleted statuses (default: False).
        """
        result = await make_request(
            "GET",
            "/api/ticket-status",
            params={"resource": resource, "includeInactive": include_inactive or None},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_ticket_status(status_id: str) -> str:
        """
        Get a single ticket status by ID.

        Args:
            status_id: The status ID.
        """
        result = await make_request("GET", f"/api/ticket-status/{status_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_ticket_status(
        name: str,
        category: str,
        resource: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        pauses_sla: Optional[bool] = None,
    ) -> str:
        """
        Create a new ticket status.

        Args:
            name: Status name e.g. 'In Progress'.
            category: Lifecycle stage — 'TO_DO', 'IN_PROGRESS', or 'DONE'.
            resource: Resource type — 'SPRINT', 'TASK', or 'PROJECT'.
            description: Optional description.
            color: Hex color e.g. '#3B82F6'.
            icon: Icon identifier.
            pauses_sla: Whether this status pauses SLA timer (default: False).
        """
        payload: dict = {
            "name": name,
            "category": category.upper(),
            "resource": resource.upper(),
        }
        if description:
            payload["description"] = description
        if color:
            payload["color"] = color
        if icon:
            payload["icon"] = icon
        if pauses_sla is not None:
            payload["pauses_sla"] = pauses_sla

        result = await make_request(
            "POST", "/api/ticket-status/create", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_ticket_status(
        status_id: str,
        name: str,
        category: str,
        resource: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        pauses_sla: Optional[bool] = None,
    ) -> str:
        """
        Update a ticket status. Name, category, and resource are all required on update.

        Args:
            status_id: The status ID.
            name: Status name.
            category: 'TO_DO', 'IN_PROGRESS', or 'DONE'.
            resource: 'SPRINT', 'TASK', or 'PROJECT'.
            description: Optional description.
            color: Hex color.
            icon: Icon identifier.
            pauses_sla: Whether this status pauses SLA timer.
        """
        payload: dict = {
            "name": name,
            "category": category.upper(),
            "resource": resource.upper(),
        }
        if description is not None:
            payload["description"] = description
        if color is not None:
            payload["color"] = color
        if icon is not None:
            payload["icon"] = icon
        if pauses_sla is not None:
            payload["pauses_sla"] = pauses_sla

        result = await make_request(
            "PUT", f"/api/ticket-status/{status_id}", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_delete_ticket_status(status_id: str) -> str:
        """
        Soft-delete a ticket status (sets inactive; data is retained).
        Will fail if active tickets are still using this status.

        Args:
            status_id: The status ID to deactivate.
        """
        result = await make_request("DELETE", f"/api/ticket-status/{status_id}")
        return json.dumps(result, indent=2)

    # ─── Ticket Priorities ──────────────────────────────────────────────────────

    @mcp.tool()
    async def wetrack_list_ticket_priorities(
        resource: Optional[str] = None,
        include_inactive: bool = False,
    ) -> str:
        """
        Get the list of ticket priorities.

        Args:
            resource: Filter by resource — 'SPRINT', 'TASK', or 'PROJECT'.
            include_inactive: Include soft-deleted priorities (default: False).
        """
        result = await make_request(
            "GET",
            "/api/ticket-priorities",
            params={"resource": resource, "includeInactive": include_inactive or None},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_ticket_priority(priority_id: str) -> str:
        """
        Get a single ticket priority by ID.

        Args:
            priority_id: The priority ID.
        """
        result = await make_request("GET", f"/api/ticket-priorities/{priority_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_ticket_priority(
        name: str,
        priority_type: str,
        resource: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> str:
        """
        Create a new ticket priority. The code is auto-derived from the name.

        Args:
            name: Priority name e.g. 'Blocker' or 'Very High'.
            priority_type: Severity bucket — 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'.
            resource: Resource type — 'SPRINT', 'TASK', or 'PROJECT'.
            description: Optional description.
            color: Hex color.
            icon: Icon identifier.
        """
        payload: dict = {
            "name": name,
            "type": priority_type.upper(),
            "resource": resource.upper(),
        }
        if description:
            payload["description"] = description
        if color:
            payload["color"] = color
        if icon:
            payload["icon"] = icon

        result = await make_request(
            "POST", "/api/ticket-priorities/create", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_ticket_priority(
        priority_id: str,
        name: str,
        priority_type: Optional[str] = None,
        resource: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> str:
        """
        Update a ticket priority by ID.

        Args:
            priority_id: The priority ID.
            name: New priority name (required — code is auto-derived from it).
            priority_type: Severity bucket — 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'.
            resource: Resource type — 'SPRINT', 'TASK', 'PROJECT'.
            description: Optional description.
            color: Hex color.
            icon: Icon identifier.
        """
        payload: dict = {"name": name}
        if priority_type:
            payload["type"] = priority_type.upper()
        if resource:
            payload["resource"] = resource.upper()
        if description is not None:
            payload["description"] = description
        if color is not None:
            payload["color"] = color
        if icon is not None:
            payload["icon"] = icon

        result = await make_request(
            "PUT", f"/api/ticket-priorities/{priority_id}", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_delete_ticket_priority(priority_id: str) -> str:
        """
        Soft-delete a ticket priority (sets inactive; data retained).
        Will fail if active tickets still use this priority.

        Args:
            priority_id: The priority ID to deactivate.
        """
        result = await make_request("DELETE", f"/api/ticket-priorities/{priority_id}")
        return json.dumps(result, indent=2)

    # ─── Ticket Categories ──────────────────────────────────────────────────────

    @mcp.tool()
    async def wetrack_list_ticket_categories() -> str:
        """Get all ticket categories."""
        result = await make_request("GET", "/api/ticket-categories")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_ticket_category(category_id: str) -> str:
        """
        Get a single ticket category by ID.

        Args:
            category_id: The category ID.
        """
        result = await make_request("GET", f"/api/ticket-categories/{category_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_ticket_category(
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> str:
        """
        Create a new ticket category.

        Args:
            name: Category name e.g. 'Hardware'.
            description: Optional description.
            color: Hex color.
            icon: Icon identifier.
        """
        payload: dict = {"name": name}
        if description:
            payload["description"] = description
        if color:
            payload["color"] = color
        if icon:
            payload["icon"] = icon

        result = await make_request(
            "POST", "/api/ticket-categories/create", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_ticket_category(
        category_id: str,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> str:
        """
        Update a ticket category.

        Args:
            category_id: The category ID.
            name: Category name (required).
            description: Optional description.
            color: Hex color.
            icon: Icon identifier.
            is_active: Active state.
        """
        payload: dict = {"name": name}
        if description is not None:
            payload["description"] = description
        if color is not None:
            payload["color"] = color
        if icon is not None:
            payload["icon"] = icon
        if is_active is not None:
            payload["is_active"] = is_active

        result = await make_request(
            "PUT", f"/api/ticket-categories/{category_id}", json=payload
        )
        return json.dumps(result, indent=2)

    # ─── Ticket Types ───────────────────────────────────────────────────────────

    @mcp.tool()
    async def wetrack_list_ticket_types() -> str:
        """Get all ticket types."""
        result = await make_request("GET", "/api/ticket-types")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_ticket_type(type_id: str) -> str:
        """
        Get a single ticket type by ID.

        Args:
            type_id: The ticket type ID.
        """
        result = await make_request("GET", f"/api/ticket-types/{type_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_ticket_type(
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> str:
        """
        Create a new ticket type.

        Args:
            name: Type name e.g. 'Bug'.
            description: Optional description.
            color: Hex color.
            icon: Icon identifier.
        """
        payload: dict = {"name": name}
        if description:
            payload["description"] = description
        if color:
            payload["color"] = color
        if icon:
            payload["icon"] = icon

        result = await make_request("POST", "/api/ticket-types/create", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_ticket_type(
        type_id: str,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> str:
        """
        Update a ticket type.

        Args:
            type_id: The ticket type ID.
            name: New name (required).
            description: New description.
            color: New hex color.
            icon: New icon identifier.
        """
        payload: dict = {"name": name}
        if description is not None:
            payload["description"] = description
        if color is not None:
            payload["color"] = color
        if icon is not None:
            payload["icon"] = icon

        result = await make_request(
            "PUT", f"/api/ticket-types/{type_id}", json=payload
        )
        return json.dumps(result, indent=2)

    # ─── Ticket Products ────────────────────────────────────────────────────────

    @mcp.tool()
    async def wetrack_list_ticket_products() -> str:
        """Get all ticket products."""
        result = await make_request("GET", "/api/ticket-products")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_ticket_product(product_id: str) -> str:
        """
        Get a single ticket product by ID.

        Args:
            product_id: The product ID.
        """
        result = await make_request("GET", f"/api/ticket-products/{product_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_ticket_product(
        name: str, description: Optional[str] = None
    ) -> str:
        """
        Create a new ticket product.

        Args:
            name: Product name e.g. 'VTrack Fleet'.
            description: Optional description.
        """
        payload: dict = {"name": name}
        if description:
            payload["description"] = description

        result = await make_request(
            "POST", "/api/ticket-products/create", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_ticket_product(
        product_id: str,
        name: str,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> str:
        """
        Update a ticket product.

        Args:
            product_id: The product ID.
            name: New name (required).
            description: New description.
            is_active: Active state.
        """
        payload: dict = {"name": name}
        if description is not None:
            payload["description"] = description
        if is_active is not None:
            payload["is_active"] = is_active

        result = await make_request(
            "PUT", f"/api/ticket-products/{product_id}", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_toggle_ticket_product(product_id: str) -> str:
        """
        Toggle the active/inactive status of a ticket product.

        Args:
            product_id: The product ID.
        """
        result = await make_request(
            "PATCH", f"/api/ticket-products/{product_id}/toggle-product"
        )
        return json.dumps(result, indent=2)

    # ─── Timezones ──────────────────────────────────────────────────────────────

    @mcp.tool()
    async def wetrack_list_timezones() -> str:
        """
        Get all available timezones.
        Use the returned integer IDs when creating clients or organisations
        that need a specific timezone.
        """
        result = await make_request("GET", "/api/timezones", auto_login=False)
        return json.dumps(result, indent=2)
