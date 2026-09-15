"""Search Tools — global search across tickets, projects, sprints, and users."""

import json
from typing import Optional
from ..client import make_request


def register_search_tools(mcp):

    @mcp.tool()
    async def wetrack_search(
        query: str,
        search_type: str = "all",
        project_id: Optional[str] = None,
        limit: int = 6,
    ) -> str:
        """
        Global search across WeTrack — tickets, projects, sprints, and users
        with weighted relevance ranking.

        Args:
            query: Search keyword or ticket code e.g. 'MOB-1', 'authentication', 'login bug'.
            search_type: Scope — 'all' (default), 'tickets', 'projects', 'sprints', or 'users'.
            project_id: Scope search to a specific project UUID.
            limit: Max results per category (1-20, default: 6).
        """
        result = await make_request(
            "GET",
            "/api/search",
            params={
                "q": query,
                "type": search_type,
                "projectId": project_id,
                "limit": limit,
            },
        )
        return json.dumps(result, indent=2)
