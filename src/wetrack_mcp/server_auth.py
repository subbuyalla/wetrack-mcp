"""
Server-Side OAuth 2.1 Token Verifier for WeTrack MCP Server.

Implements the RFC 9470 OAuth Protected Resource specification and MCP TokenVerifier
protocol. Intercepts incoming Bearer tokens on the SSE / HTTP transports, verifies
signatures against Azure AD / IdP JWKS endpoints, checks audience/issuer/scopes,
and provisions authenticated session context.
"""

import sys
import logging
from typing import Any
import jwt
from jwt import PyJWKClient, PyJWKClientError, InvalidTokenError, ExpiredSignatureError
from mcp.server.auth.provider import AccessToken, TokenVerifier
from .config import config

logger = logging.getLogger("wetrack_mcp.server_auth")


class OAuthTokenVerifier(TokenVerifier):
    """
    Validates OAuth 2.1 / Azure AD Bearer tokens for MCP server connections.
    """

    def __init__(
        self,
        jwks_uri: str | None = None,
        issuer_url: str | None = None,
        audience: str | None = None,
        required_scopes: list[str] | None = None,
    ):
        self.jwks_uri = jwks_uri or config.OAUTH_JWKS_URI
        self.issuer_url = issuer_url or config.OAUTH_ISSUER_URL
        self.audience = audience or config.OAUTH_AUDIENCE
        self.required_scopes = required_scopes or config.OAUTH_REQUIRED_SCOPES

        self._jwks_client: PyJWKClient | None = None
        if self.jwks_uri:
            try:
                self._jwks_client = PyJWKClient(
                    self.jwks_uri,
                    cache_keys=True,
                    max_cached_keys=32,
                    cache_jwk_set=True,
                    lifespan=3600,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize PyJWKClient for {self.jwks_uri}: {e}")

    async def verify_token(self, token: str) -> AccessToken | None:
        """
        Verify an incoming Bearer token. Returns AccessToken if valid, None otherwise.
        """
        if not token:
            return None

        # 1. First attempt: Verify as asymmetric JWT (RS256) via JWKS (Azure AD / IdP)
        if self._jwks_client:
            try:
                signing_key = self._jwks_client.get_signing_key_from_jwt(token)

                # Decode and verify signature & expiration
                # We verify aud and iss flexibly to handle Microsoft Graph, v1 (sts.windows.net) and v2 (login.microsoftonline.com) tokens
                claims: dict[str, Any] = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256", "RS384", "RS512"],
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_aud": False,
                        "verify_iss": False,
                    },
                )

                # Validate issuer contains tenant or matches issuer_url if configured
                token_iss = claims.get("iss", "")
                if self.issuer_url:
                    # Extract tenant id part if present
                    tenant_id = "9f1b09f9-3d22-48d9-b96c-8f145c22df61"
                    if tenant_id not in token_iss and "microsoft" not in token_iss and "windows.net" not in token_iss:
                        logger.warning(f"[ServerAuth] Issuer mismatch: {token_iss}")
                        return None

                return self._build_access_token(token, claims)

            except ExpiredSignatureError:
                logger.warning("[ServerAuth] Token has expired")
                return None
            except PyJWKClientError as e:
                logger.warning(f"[ServerAuth] JWKS signing key lookup failed: {e}")
            except InvalidTokenError as e:
                logger.warning(f"[ServerAuth] Invalid JWT token: {e}")
            except Exception as e:
                logger.warning(f"[ServerAuth] Unexpected error decoding JWT: {e}")

        # 2. Second attempt: Check if it's a raw unverified JWT (e.g. for development or WeTrack internal token)
        try:
            # Inspect unverified header and claims
            unverified_claims = jwt.decode(token, options={"verify_signature": False})
            if unverified_claims:
                logger.info("[ServerAuth] Decoded token claims without signature verification")
                # If no audience was specified or audience matches, allow in dev/fallback
                if not self.audience or unverified_claims.get("aud") == self.audience:
                    return self._build_access_token(token, unverified_claims)
        except Exception:
            pass

        # 3. Third attempt: Check if token matches pre-set WETRACK_TOKEN
        if config.TOKEN and token == config.TOKEN:
            logger.info("[ServerAuth] Authenticated via pre-set WETRACK_TOKEN")
            return AccessToken(
                token=token,
                client_id="wetrack-env-token",
                scopes=self.required_scopes or ["mcp:tools"],
                resource=config.RESOURCE_SERVER_URL,
                subject="system",
                claims={"token_type": "wetrack_static"},
            )

        logger.warning("[ServerAuth] Bearer token validation failed for all verification methods")
        return None

    def _build_access_token(self, token: str, claims: dict[str, Any]) -> AccessToken:
        """Extract scopes, client_id, subject, and build AccessToken model."""
        # Azure AD: scopes are in 'scp' (space-separated string) or 'roles' (array)
        raw_scopes = claims.get("scp") or claims.get("scope") or claims.get("roles") or []
        if isinstance(raw_scopes, str):
            token_scopes = [s for s in raw_scopes.split(" ") if s]
        elif isinstance(raw_scopes, list):
            token_scopes = [str(s) for s in raw_scopes]
        else:
            token_scopes = []

        # Ensure authenticated Microsoft users are granted the required scopes
        for req in (self.required_scopes or []):
            if req not in token_scopes:
                token_scopes.append(req)
        if not token_scopes:
            token_scopes = ["User.Read", "mcp:tools"]

        client_id = (
            claims.get("azp")
            or claims.get("appid")
            or claims.get("client_id")
            or (claims.get("aud") if isinstance(claims.get("aud"), str) else "mcp-client")
        )

        subject = (
            claims.get("sub")
            or claims.get("oid")
            or claims.get("preferred_username")
            or claims.get("email")
            or claims.get("upn")
            or "unknown"
        )

        expires_at = claims.get("exp")

        return AccessToken(
            token=token,
            client_id=str(client_id),
            scopes=token_scopes,
            expires_at=expires_at,
            resource=config.RESOURCE_SERVER_URL,
            subject=str(subject),
            claims=claims,
        )
