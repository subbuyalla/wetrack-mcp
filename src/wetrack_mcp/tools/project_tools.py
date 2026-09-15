"""Project Tools — full project lifecycle, files, folders, team, analytics."""

import json
from typing import Optional
from ..client import make_request


def register_project_tools(mcp):

    @mcp.tool()
    async def wetrack_list_projects(
        minimal: Optional[bool] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> str:
        """
        List projects with filtering, search, and pagination.

        Args:
            minimal: If True, returns lightweight {id, name} list for dropdowns.
            search: Search by name, key, description, or manager name.
            status: Filter by status — 'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD'.
            start_date: Filter projects starting on/after this date (YYYY-MM-DD).
            end_date: Filter projects ending on/before this date (YYYY-MM-DD).
            sort: Sort field — 'name', 'key', 'status', 'start_date', 'end_date', 'created_at'.
            order: Sort direction — 'asc' or 'desc'.
            page: Page number (default: 1).
            limit: Items per page (default: 10).
        """
        result = await make_request(
            "GET",
            "/api/projects",
            params={
                "minimal": minimal,
                "search": search,
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
                "sort": sort,
                "order": order,
                "page": page,
                "limit": limit,
            },
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_project(project_id: str) -> str:
        """
        Get full details of a single project.

        Args:
            project_id: The project UUID.
        """
        result = await make_request("GET", f"/api/projects/{project_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_project(
        name: str,
        key: str,
        start_date: str,
        end_date: str,
        manager_id: Optional[str] = None,
        description: Optional[str] = None,
        sprint_duration_weeks: Optional[int] = None,
        color: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> str:
        """
        Create a new project. Sprints are auto-generated from the timeline.

        Args:
            name: Project name e.g. 'WeTrack Platform'.
            key: Short unique key e.g. 'WTP' (used as ticket prefix).
            start_date: Project start date — 'YYYY-MM-DD'.
            end_date: Project end date — 'YYYY-MM-DD'.
            manager_id: UUID of the project manager user.
            description: Project description text.
            sprint_duration_weeks: Sprint length in weeks (default: 2).
            color: Hex color for the project card e.g. '#10B981'.
            tags: List of tag strings e.g. ['Internal', 'Platform'].
        """
        payload: dict = {
            "name": name,
            "key": key,
            "startDate": start_date,
            "endDate": end_date,
        }
        if manager_id:
            payload["managerId"] = manager_id
        if description:
            payload["description"] = description
        if sprint_duration_weeks is not None:
            payload["sprintDurationWeeks"] = sprint_duration_weeks
        if color:
            payload["color"] = color
        if tags:
            payload["tags"] = tags

        result = await make_request("POST", "/api/projects", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_update_project(
        project_id: str,
        name: Optional[str] = None,
        manager_id: Optional[str] = None,
        description: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sprint_duration_weeks: Optional[int] = None,
        color: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> str:
        """
        Update a project's fields (partial update — only send what changes).
        Changing timeline recalculates sprints automatically.

        Args:
            project_id: The project UUID.
            name: New project name.
            manager_id: UUID of new project manager.
            description: New description.
            start_date: New start date 'YYYY-MM-DD'.
            end_date: New end date 'YYYY-MM-DD'.
            sprint_duration_weeks: New sprint duration in weeks.
            color: New hex color.
            tags: New tag list (replaces existing).
        """
        payload = {}
        if name is not None:
            payload["name"] = name
        if manager_id is not None:
            payload["managerId"] = manager_id
        if description is not None:
            payload["description"] = description
        if start_date is not None:
            payload["startDate"] = start_date
        if end_date is not None:
            payload["endDate"] = end_date
        if sprint_duration_weeks is not None:
            payload["sprintDurationWeeks"] = sprint_duration_weeks
        if color is not None:
            payload["color"] = color
        if tags is not None:
            payload["tags"] = tags

        result = await make_request("PATCH", f"/api/projects/{project_id}", json=payload)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_delete_project(project_id: str) -> str:
        """
        Soft-delete a project (it becomes inactive but data is retained).

        Args:
            project_id: The project UUID to delete.
        """
        result = await make_request("DELETE", f"/api/projects/{project_id}")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_recent_projects(limit: int = 4) -> str:
        """
        Get the most recently accessed projects for the authenticated user.

        Args:
            limit: Max projects to return (1-10, default: 4).
        """
        result = await make_request(
            "GET", "/api/projects/recent", params={"limit": limit}
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_project_stats(
        top_limit: int = 5, deadlines_limit: int = 3
    ) -> str:
        """
        Get dashboard statistics — summary totals, top projects by progress,
        and upcoming project deadlines.

        Args:
            top_limit: Number of top projects to return (default: 5).
            deadlines_limit: Number of upcoming deadlines to return (default: 3).
        """
        result = await make_request(
            "GET",
            "/api/projects/stats",
            params={"top_limit": top_limit, "deadlines_limit": deadlines_limit},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_project_overview(project_id: str) -> str:
        """
        Get the complete overview dashboard analytics for a project —
        includes KPIs, ticket distributions, team stats, and progress.

        Args:
            project_id: The project UUID.
        """
        result = await make_request("GET", f"/api/projects/{project_id}/overview")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_project_reports(
        project_id: str, sprint_id: Optional[str] = None
    ) -> str:
        """
        Get comprehensive reports and analytics for a project.

        Args:
            project_id: The project UUID.
            sprint_id: Optional sprint UUID to scope stats to a specific sprint.
        """
        result = await make_request(
            "GET",
            f"/api/projects/{project_id}/reports",
            params={"sprint_id": sprint_id},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_project_users(project_id: str) -> str:
        """
        Get all team members mapped to a project (derived from ticket assignees).
        Returns {id, name, email, role, designation} per user.

        Args:
            project_id: The project UUID.
        """
        result = await make_request("GET", f"/api/projects/{project_id}/users")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_project_sprints(project_id: str) -> str:
        """
        Get all sprints for a project including statistics and progress metrics.

        Args:
            project_id: The project UUID.
        """
        result = await make_request("GET", f"/api/projects/{project_id}/sprints")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_record_project_access(project_id: str) -> str:
        """
        Record that the current user accessed a project (updates 'recently accessed' list).

        Args:
            project_id: The project UUID.
        """
        result = await make_request("POST", f"/api/projects/{project_id}/access")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_list_project_files(
        project_id: str,
        folder_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> str:
        """
        Get all files, folders, and ticket attachments for a project with storage stats.

        Args:
            project_id: The project UUID.
            folder_id: Filter to a specific folder UUID (pass 'root' or omit for root level).
            search: Search files/folders by name.
        """
        result = await make_request(
            "GET",
            f"/api/projects/{project_id}/files",
            params={"folderId": folder_id, "search": search},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_add_project_file(
        project_id: str,
        file_name: str,
        file_size: float,
        s3_url: str,
        file_type: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> str:
        """
        Register an already-uploaded S3 file in project files.
        Upload to S3 first using wetrack_get_upload_presign_url, then call this.

        Args:
            project_id: The project UUID.
            file_name: The file name e.g. 'requirements.pdf'.
            file_size: File size in bytes.
            s3_url: The S3 URL returned from the upload.
            file_type: MIME type e.g. 'application/pdf'.
            folder_id: UUID of the folder to place the file in.
        """
        payload: dict = {
            "fileName": file_name,
            "fileSize": file_size,
            "s3Url": s3_url,
        }
        if file_type:
            payload["fileType"] = file_type
        if folder_id:
            payload["folderId"] = folder_id
        result = await make_request(
            "POST", f"/api/projects/{project_id}/files", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_delete_project_file(project_id: str, file_id: str) -> str:
        """
        Delete a project file record.

        Args:
            project_id: The project UUID.
            file_id: The file UUID to delete.
        """
        result = await make_request(
            "DELETE", f"/api/projects/{project_id}/files/{file_id}"
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_create_project_folder(
        project_id: str,
        name: str,
        parent_folder_id: Optional[str] = None,
    ) -> str:
        """
        Create a folder (or sub-folder) inside a project's file storage.

        Args:
            project_id: The project UUID.
            name: Folder name e.g. '01. Requirements'.
            parent_folder_id: UUID of parent folder for sub-folders.
        """
        payload: dict = {"name": name}
        if parent_folder_id:
            payload["parentFolderId"] = parent_folder_id
        result = await make_request(
            "POST", f"/api/projects/{project_id}/folders", json=payload
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_delete_project_folder(
        project_id: str, folder_id: str
    ) -> str:
        """
        Delete a folder from a project.

        Args:
            project_id: The project UUID.
            folder_id: The folder UUID to delete.
        """
        result = await make_request(
            "DELETE", f"/api/projects/{project_id}/folders/{folder_id}"
        )
        return json.dumps(result, indent=2)
