"""Client & Organisation Tools — manage client orgs and their members."""

import json
from typing import Optional
from ..client import make_request


def register_client_tools(mcp):

    @mcp.tool()
    async def wetrack_list_clients() -> str:
        """
        Retrieve list of all client organisations accessible by the current user.
        """
        result = await make_request("GET", "/api/clients")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_client(client_id: str) -> str:
        """
        Get details of a specific client organisation.

        Args:
            client_id: The client/organisation ID.
        """
        result = await make_request("GET", f"/api/clients/{client_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_client(
        name: str,
        email: str,
        contact_name: str,
        address: str,
        phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        code: Optional[str] = None,
        country: Optional[str] = None,
        timezone_id: Optional[int] = None,
    ) -> str:
        """
        Create a new client organisation.

        Args:
            name: Organisation name e.g. 'Acme Corp'.
            email: Primary contact email e.g. 'contact@acme.com'.
            contact_name: Primary contact person name e.g. 'John Doe'.
            address: Physical address e.g. '123 Tech Park'.
            phone: Organisation phone number.
            contact_email: Contact person's email (if different from org email).
            contact_phone: Contact person's phone.
            code: Short org code e.g. 'AC'.
            country: Country name.
            timezone_id: Timezone integer ID (get from wetrack_list_timezones).
        """
        payload: dict = {
            "name": name,
            "email": email,
            "contact_name": contact_name,
            "address": address,
        }
        if phone:
            payload["phone"] = phone
        if contact_email:
            payload["contact_email"] = contact_email
        if contact_phone:
            payload["contact_phone"] = contact_phone
        if code:
            payload["code"] = code
        if country:
            payload["country"] = country
        if timezone_id is not None:
            payload["timezone_id"] = timezone_id

        result = await make_request("POST", "/api/clients/create", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_client(
        client_id: str,
        name: str,
        email: str,
        phone: Optional[str] = None,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        address: Optional[str] = None,
        country: Optional[str] = None,
        timezone_id: Optional[int] = None,
    ) -> str:
        """
        Update a client organisation's details.

        Args:
            client_id: The client ID.
            name: Organisation name (required).
            email: Primary email (required).
            phone: Phone number.
            contact_name: Primary contact person name.
            contact_email: Contact email.
            contact_phone: Contact phone.
            address: Physical address.
            country: Country name.
            timezone_id: Timezone integer ID.
        """
        payload: dict = {"name": name, "email": email}
        if phone:
            payload["phone"] = phone
        if contact_name:
            payload["contact_name"] = contact_name
        if contact_email:
            payload["contact_email"] = contact_email
        if contact_phone:
            payload["contact_phone"] = contact_phone
        if address:
            payload["address"] = address
        if country:
            payload["country"] = country
        if timezone_id is not None:
            payload["timezone_id"] = timezone_id

        result = await make_request("PUT", f"/api/clients/{client_id}", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_add_client_members(
        client_id: str, member_ids: list[int]
    ) -> str:
        """
        Assign or update the members associated with a client organisation.

        Args:
            client_id: The client ID.
            member_ids: List of integer user IDs to associate with this client
                        e.g. [1, 2, 5].
        """
        result = await make_request(
            "POST",
            f"/api/clients/{client_id}/add-members",
            json={"members": member_ids},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_list_organisations() -> str:
        """
        Retrieve the list of all organisations in the system.
        """
        result = await make_request("GET", "/api/organisations")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_organisation(
        name: str,
        email: str,
        contact_name: str,
        slug: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> str:
        """
        Create a new organisation.

        Args:
            name: Organisation name e.g. 'Vithi IT Solutions'.
            email: Contact email e.g. 'contact@vithi.com'.
            contact_name: Primary contact person e.g. 'Jane Doe'.
            slug: URL slug e.g. 'vithi'.
            phone: Phone number.
        """
        payload: dict = {
            "name": name,
            "email": email,
            "contactName": contact_name,
        }
        if slug:
            payload["slug"] = slug
        if phone:
            payload["phone"] = phone

        result = await make_request("POST", "/api/organisations", json=payload)
        return json.dumps(result, indent=2)
