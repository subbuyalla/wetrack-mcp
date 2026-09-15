"""User Tools — create, list, update users and manage invitations."""

import json
from typing import Optional
from ..client import make_request


def register_user_tools(mcp):

    @mcp.tool()
    async def wetrack_list_users(
        role: Optional[str] = None,
        is_dropdown: Optional[bool] = None,
    ) -> str:
        """
        Retrieve the list of users in the organisation.

        Args:
            role: Filter by role — 'ADMIN', 'VITHI_USER', 'EMPLOYEE', 'CUSTOMER'.
            is_dropdown: If True, returns lightweight {id, name} for dropdowns.
                         If False/omitted, returns full user details including designation.
        """
        result = await make_request(
            "GET",
            "/api/users",
            params={"role": role, "isDropdown": is_dropdown},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_user(user_id: str) -> str:
        """
        Get a single user's details by their ID.

        Args:
            user_id: The user UUID or integer ID.
        """
        result = await make_request("GET", f"/api/users/{user_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_user(
        first_name: str,
        last_name: str,
        email: str,
        role: str,
        designation: str,
        user_name: Optional[str] = None,
    ) -> str:
        """
        Create a single user account and send an invitation email.

        Args:
            first_name: User's first name e.g. 'Jane'.
            last_name: User's last name e.g. 'Smith'.
            email: User's email e.g. 'jane@company.com'.
            role: Access role — 'ADMIN', 'VITHI_USER', 'EMPLOYEE', or 'CUSTOMER'.
            designation: Job title e.g. 'Senior Backend Engineer'.
            user_name: Optional username override.
        """
        payload: dict = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role": role,
            "designation": designation,
        }
        if user_name:
            payload["user_name"] = user_name
        result = await make_request("POST", "/api/users/create", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_bulk_create_users(
        users: list[dict],
        skip_invite_email: bool = False,
    ) -> str:
        """
        Bulk create multiple user accounts at once.

        Args:
            users: List of user objects. Each must have:
                   {first_name, last_name, email, role} — and optionally user_name.
            skip_invite_email: Set True for SSO-only users who won't use password login.

        Example users list:
            [
              {"first_name": "Alice", "last_name": "Wong", "email": "alice@co.com", "role": "VITHI_USER"},
              {"first_name": "Bob", "last_name": "Jones", "email": "bob@co.com", "role": "EMPLOYEE"}
            ]
        """
        result = await make_request(
            "POST",
            "/api/users/create-users",
            json={"users": users, "skipInviteEmail": skip_invite_email},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_user(
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: Optional[str] = None,
        designation: Optional[str] = None,
    ) -> str:
        """
        Update a user's profile fields.

        Args:
            user_id: The user UUID or integer ID.
            first_name: New first name.
            last_name: New last name.
            role: New role — 'ADMIN', 'VITHI_USER', 'EMPLOYEE', 'CUSTOMER'.
            designation: New job title. Cannot be an empty string.
        """
        payload = {}
        if first_name is not None:
            payload["first_name"] = first_name
        if last_name is not None:
            payload["last_name"] = last_name
        if role is not None:
            payload["role"] = role
        if designation is not None:
            payload["designation"] = designation

        result = await make_request("PUT", f"/api/users/{user_id}", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_resend_invite(user_id: str) -> str:
        """
        Resend the invitation email to a user who hasn't set their password yet.

        Args:
            user_id: The user UUID or integer ID.
        """
        result = await make_request(
            "POST",
            "/api/users/resend-invite",
            json={"user_id": user_id},
        )
        return json.dumps(result, indent=2)
