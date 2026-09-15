"""Metadata Field Tools — custom field definitions for TICKET, PROJECT, and SPRINT."""

import json
from typing import Optional
from ..client import make_request


def register_metadata_tools(mcp):

    @mcp.tool()
    async def wetrack_list_metadata_fields(
        resource_type: Optional[str] = None,
        ticket_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        limit: int = 10,
    ) -> str:
        """
        Get all custom metadata field definitions.

        Args:
            resource_type: Filter by resource — 'TICKET', 'PROJECT', or 'SPRINT'.
            ticket_type: Filter by ticket type — 'EPIC', 'STORY', 'TASK', 'BUG'.
                         Only meaningful when resource_type is 'TICKET'.
            is_active: Filter by active status.
            page: Page number (default: 1).
            limit: Items per page (default: 10).
        """
        result = await make_request(
            "GET",
            "/api/metadata-fields",
            params={
                "resource_type": resource_type,
                "ticket_type": ticket_type,
                "is_active": is_active,
                "page": page,
                "limit": limit,
            },
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_metadata_field(field_id: int) -> str:
        """
        Get a single metadata field definition by ID.

        Args:
            field_id: Integer ID of the metadata field.
        """
        result = await make_request("GET", f"/api/metadata-fields/{field_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_metadata_field(
        resource_type: str,
        label: str,
        field_type: str,
        ticket_type: Optional[str] = None,
        helper_text: Optional[str] = None,
        is_required: bool = False,
        options: Optional[list[dict]] = None,
    ) -> str:
        """
        Create a new custom metadata field definition.

        Args:
            resource_type: What the field belongs to — 'TICKET', 'PROJECT', or 'SPRINT'.
            label: Field label e.g. 'Cost Center'.
            field_type: Field input type — 'TEXT', 'NUMBER', 'DATE', 'BOOLEAN',
                        'SELECT', or 'MULTI_SELECT'.
            ticket_type: Required when resource_type is 'TICKET' — 'EPIC', 'STORY', 'TASK', 'BUG'.
            helper_text: Optional placeholder/helper text shown below the field.
            is_required: Whether this field is mandatory (default: False).
            options: Required for SELECT/MULTI_SELECT fields — list of option objects:
                     [{"label": "Engineering", "value": "eng"}, ...]

        Example:
            resource_type="TICKET", ticket_type="BUG", label="Environment",
            field_type="SELECT", options=[{"label": "Production", "value": "prod"},
                                          {"label": "Staging", "value": "staging"}]
        """
        payload: dict = {
            "resourceType": resource_type.upper(),
            "label": label,
            "fieldType": field_type.upper(),
            "isRequired": is_required,
        }
        if ticket_type:
            payload["ticketType"] = ticket_type.upper()
        if helper_text:
            payload["helperText"] = helper_text
        if options:
            payload["options"] = options

        result = await make_request(
            "POST", "/api/metadata-fields/create", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_metadata_field(
        field_id: int,
        label: str,
        helper_text: Optional[str] = None,
        is_required: Optional[bool] = None,
        options: Optional[list[dict]] = None,
    ) -> str:
        """
        Update an existing metadata field definition.

        Args:
            field_id: Integer ID of the metadata field.
            label: New field label (required).
            helper_text: New helper text.
            is_required: New required state.
            options: New options list for SELECT/MULTI_SELECT fields:
                     [{"label": "...", "value": "..."}, ...]
        """
        payload: dict = {"label": label}
        if helper_text is not None:
            payload["helperText"] = helper_text
        if is_required is not None:
            payload["isRequired"] = is_required
        if options is not None:
            payload["options"] = options

        result = await make_request(
            "PUT", f"/api/metadata-fields/{field_id}", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_delete_metadata_field(field_id: int) -> str:
        """
        Delete a metadata field definition.
        Will fail for system-protected fields.

        Args:
            field_id: Integer ID of the metadata field to delete.
        """
        result = await make_request("DELETE", f"/api/metadata-fields/{field_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_toggle_metadata_field_status(field_id: int) -> str:
        """
        Toggle a metadata field's active/inactive status.

        Args:
            field_id: Integer ID of the metadata field.
        """
        result = await make_request(
            "PATCH", f"/api/metadata-fields/{field_id}/toggle-status"
        )
        return json.dumps(result, indent=2)
