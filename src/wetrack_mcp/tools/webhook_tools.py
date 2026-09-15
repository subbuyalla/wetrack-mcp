"""
Webhook & Cron Tools — system-level integrations.

These endpoints are called by external schedulers (cron jobs) and
webhook providers (Resend email inbound). They require special auth headers:

- SLA breach trigger:           POST /api/sla              (auth-key header)
- Sprint burndown snapshot:     POST /api/cron/sprint-burndown-snapshot (auth-key header)
- Inbound email webhook:        POST /api/webhooks/listenEmails (Svix headers)

The auth-key is a secret shared with the scheduler and is separate from
the user Bearer JWT. Set it in .env as WETRACK_AUTH_KEY.
"""

import json
import os
from typing import Optional
from ..client import make_request


def register_webhook_tools(mcp):

    @mcp.tool()
    async def wetrack_trigger_sla_check(
        breach_count: int,
        auth_key: Optional[str] = None,
    ) -> str:
        """
        [System/Admin] Trigger the SLA breach notification check.
        Normally called by an automated scheduler — this tool lets you
        trigger it manually for testing or on-demand checks.

        Args:
            breach_count: Number of SLA breaches to process e.g. 3.
            auth_key: System auth key (WETRACK_AUTH_KEY from .env).
                      If not provided, reads from WETRACK_AUTH_KEY env var.

        Note: This requires the WETRACK_AUTH_KEY environment variable to be set,
        not the regular user JWT. Contact your WeTrack admin for this key.
        """
        key = auth_key or os.getenv("WETRACK_AUTH_KEY", "")
        if not key:
            return json.dumps({
                "success": False,
                "message": (
                    "WETRACK_AUTH_KEY not set. Add it to your .env file. "
                    "This is a system-level secret provided by your WeTrack administrator."
                ),
            }, indent=2)

        import httpx
        from ..config import config

        async with httpx.AsyncClient(base_url=config.BASE_URL, timeout=30.0) as client:
            response = await client.post(
                "/api/sla",
                json={"breachCount": breach_count},
                headers={"auth-key": key},
            )
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}

        return json.dumps({
            "success": 200 <= response.status_code < 300,
            "status_code": response.status_code,
            "data": body,
        }, indent=2)

    @mcp.tool()
    async def wetrack_trigger_sprint_burndown_snapshot(
        auth_key: Optional[str] = None,
    ) -> str:
        """
        [System/Admin] Snapshot today's remaining scope for every active sprint.
        Normally called by an automated daily scheduler — this tool lets you
        trigger it manually for testing or to backfill a missed snapshot.

        Args:
            auth_key: System auth key (WETRACK_AUTH_KEY from .env).
                      If not provided, reads from WETRACK_AUTH_KEY env var.

        Note: This requires the WETRACK_AUTH_KEY, not the regular user JWT.
        """
        key = auth_key or os.getenv("WETRACK_AUTH_KEY", "")
        if not key:
            return json.dumps({
                "success": False,
                "message": (
                    "WETRACK_AUTH_KEY not set. Add it to your .env file. "
                    "This is a system-level secret provided by your WeTrack administrator."
                ),
            }, indent=2)

        import httpx
        from ..config import config

        async with httpx.AsyncClient(base_url=config.BASE_URL, timeout=30.0) as client:
            response = await client.post(
                "/api/cron/sprint-burndown-snapshot",
                headers={"auth-key": key},
            )
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}

        return json.dumps({
            "success": 200 <= response.status_code < 300,
            "status_code": response.status_code,
            "data": body,
        }, indent=2)

    @mcp.tool()
    async def wetrack_get_webhook_info() -> str:
        """
        Get information about the WeTrack inbound email webhook endpoint.
        This endpoint is called by Resend (or any Svix-compatible provider)
        when an inbound email is received and creates a ticket automatically.

        Returns documentation about the webhook setup rather than calling
        the endpoint (which requires Svix signature headers from the provider).
        """
        return json.dumps({
            "success": True,
            "data": {
                "endpoint": "POST /api/webhooks/listenEmails",
                "provider": "Resend (via Svix)",
                "required_headers": {
                    "svix-id": "Unique message ID from Svix",
                    "svix-timestamp": "Unix timestamp of the webhook",
                    "svix-signature": "HMAC signature for verification",
                },
                "description": (
                    "Receives inbound emails from Resend and creates WeTrack tickets "
                    "automatically. Configure your Resend inbound email webhook to "
                    "point to: https://wetrack-two.vercel.app/api/webhooks/listenEmails"
                ),
                "setup_steps": [
                    "1. Go to Resend dashboard → Webhooks.",
                    "2. Add endpoint: https://wetrack-two.vercel.app/api/webhooks/listenEmails",
                    "3. Select 'email.received' event.",
                    "4. Resend will sign requests with a secret — set it as WETRACK_SVIX_SECRET in WeTrack's env.",
                ],
                "error_responses": {
                    "401": "Invalid webhook signature",
                    "403": "Missing Svix headers or webhook secret not configured",
                    "500": "Server error processing the email",
                },
            },
        }, indent=2)
