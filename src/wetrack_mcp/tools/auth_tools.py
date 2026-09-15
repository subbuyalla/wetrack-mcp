"""Auth Tools — sign-in, sign-out, password management, impersonation."""

import json
from ..auth import auth_manager
from ..client import make_request


def register_auth_tools(mcp):

    @mcp.tool()
    async def wetrack_sign_in(email: str, password: str) -> str:
        """
        Sign in to WeTrack with email and password.
        Returns a JWT token stored for all future requests.
        Use this first if you haven't set WETRACK_EMAIL/PASSWORD in .env.
        """
        result = await auth_manager.sign_in(email=email, password=password)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_sign_out() -> str:
        """Sign out from WeTrack and clear the current session token."""
        result = await auth_manager.sign_out()
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_get_current_user() -> str:
        """
        Get the currently authenticated user's profile and sidebar permissions.
        Useful to verify who is logged in and what their role is.
        """
        result = await make_request("GET", "/api/users/current-user")
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_change_password(
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> str:
        """
        Change the logged-in user's password.

        Args:
            current_password: The user's current password.
            new_password: The new password to set.
            confirm_password: Must match new_password exactly.
        """
        result = await make_request(
            "POST",
            "/api/auth/change-password",
            json={
                "currentPassword": current_password,
                "newPassword": new_password,
                "confirmPassword": confirm_password,
            },
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_forgot_password(email: str) -> str:
        """
        Trigger a password reset email for a user.

        Args:
            email: The email address of the user who forgot their password.
        """
        result = await make_request(
            "POST",
            "/api/auth/forgot-password",
            json={"email": email},
            auto_login=False,
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_set_password(password: str) -> str:
        """
        Set the initial password for the currently authenticated user
        (used during first-time login flows).

        Args:
            password: The new password to set.
        """
        result = await make_request(
            "POST",
            "/api/auth/set-password",
            json={"password": password},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_impersonate(target_user_id: str) -> str:
        """
        [Admin only] Start an impersonation session — log in AS another user.
        Use wetrack_exit_impersonation to restore the admin session.

        Args:
            target_user_id: UUID of the user to impersonate.
        """
        result = await make_request(
            "POST",
            "/api/auth/impersonate",
            json={"targetUserId": target_user_id},
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def wetrack_exit_impersonation() -> str:
        """
        Exit the current impersonation session and restore the administrator session.
        Only works if you previously called wetrack_impersonate.
        """
        result = await make_request("POST", "/api/auth/impersonate/exit")
        return json.dumps(result, indent=2)
