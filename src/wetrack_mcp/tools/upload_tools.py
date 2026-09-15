"""
Upload Tools — S3 presigned URL generation and direct file upload.

Two-step upload flow:
  1. Call wetrack_get_upload_presign_url → get a pre-signed S3 PUT URL + final file URL
  2. PUT the file binary directly to the S3 presigned URL (browser/client side)
  3. Use the final S3 URL when calling wetrack_add_ticket_attachment or
     wetrack_add_project_file

Alternatively, for small files via the MCP server itself:
  Use wetrack_upload_file (multipart, max 5MB) which handles step 1+2 internally.
"""

import json
from typing import Optional
from ..client import make_request


def register_upload_tools(mcp):

    @mcp.tool()
    async def wetrack_get_upload_presign_url(
        file_name: str,
        file_type: str,
    ) -> str:
        """
        Generate an S3 pre-signed upload URL for direct browser-side file uploads.

        This is step 1 of the two-step upload flow:
          1. Call this to get a presigned PUT URL and the final S3 file URL.
          2. The client/browser PUTs the file binary directly to the presigned URL.
          3. Use the final S3 URL in wetrack_add_ticket_attachment or
             wetrack_add_project_file to register the file in WeTrack.

        Args:
            file_name: Original file name e.g. 'screenshot.png', 'report.pdf'.
            file_type: MIME type e.g. 'image/png', 'application/pdf', 'video/mp4'.

        Returns:
            presignedUrl: The S3 PUT URL to upload the file to (expires in ~15 min).
            url: The final public S3 URL to use as the attachment URL in WeTrack.
        """
        result = await make_request(
            "POST",
            "/api/upload/presign",
            json={"fileName": file_name, "fileType": file_type},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_upload_instructions() -> str:
        """
        Get instructions on how to upload files to WeTrack via S3.

        Since MCP cannot directly stream binary files, this tool explains
        the complete upload workflow so you can guide the user correctly.
        """
        return json.dumps({
            "success": True,
            "data": {
                "upload_methods": {
                    "method_1_presigned_url": {
                        "description": "Best for large files or browser uploads",
                        "steps": [
                            "1. Call wetrack_get_upload_presign_url(file_name, file_type) to get a presigned S3 PUT URL.",
                            "2. Client/browser sends an HTTP PUT request to the presignedUrl with the file binary as the body.",
                            "   PUT <presignedUrl>",
                            "   Content-Type: <file_type>",
                            "   Body: <raw file bytes>",
                            "3. Use the returned 'url' (final S3 URL) in wetrack_add_ticket_attachment or wetrack_add_project_file.",
                        ],
                        "limits": "No size limit (S3 direct)",
                    },
                    "method_2_multipart_api": {
                        "description": "For files <= 5MB, upload directly via the WeTrack API",
                        "endpoint": "POST /api/upload",
                        "content_type": "multipart/form-data",
                        "field": "file (binary)",
                        "limit": "5MB max",
                        "returns": "{ location: 'https://bucket.s3.region.amazonaws.com/...' }",
                        "note": "MCP cannot stream binary files directly. Use this from your app code.",
                    },
                },
                "after_upload": {
                    "ticket_attachment": "Call wetrack_add_ticket_attachment(ticket_id, url, file_name, file_size)",
                    "project_file": "Call wetrack_add_project_file(project_id, file_name, file_size, s3_url)",
                },
            },
        }, indent=2)
