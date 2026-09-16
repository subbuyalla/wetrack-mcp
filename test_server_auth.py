"""
Test suite for Server-Side OAuth 2.1 authentication on WeTrack MCP server.
Verifies RFC 9470 protected resource metadata, 401 challenge, and token validation.
"""

import os
import json
import jwt
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from starlette.testclient import TestClient

# Ensure test environment variables
os.environ["OAUTH_ENABLED"] = "true"
os.environ["MCP_TRANSPORT"] = "sse"
os.environ["MCP_RESOURCE_SERVER_URL"] = "http://16.112.106.229:8000"
os.environ["OAUTH_ISSUER_URL"] = "https://login.microsoftonline.com/organizations/v2.0"
os.environ["OAUTH_AUDIENCE"] = "47722668-aafe-422a-a167-10c32d67c2f0"
os.environ["OAUTH_REQUIRED_SCOPES"] = "mcp:tools"

from src.wetrack_mcp.server import mcp
from src.wetrack_mcp.config import config


def test_protected_resource_metadata():
    """Verify RFC 9470 /.well-known/oauth-protected-resource endpoint."""
    app = mcp.sse_app()
    client = TestClient(app)

    res = client.get("/.well-known/oauth-protected-resource")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    
    data = res.json()
    assert data["resource"].rstrip("/") == "http://16.112.106.229:8000"
    assert "https://login.microsoftonline.com/organizations/v2.0" in data["authorization_servers"]
    assert "mcp:tools" in data["scopes_supported"]
    assert "header" in data["bearer_methods_supported"]
    print("PASS: test_protected_resource_metadata")


def test_unauthenticated_request_rejected():
    """Verify unauthenticated SSE connection is rejected with 401 and RFC 9470 challenge."""
    app = mcp.sse_app()
    client = TestClient(app)

    res = client.get("/sse")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
    
    www_auth = res.headers.get("www-authenticate", "")
    assert "Bearer" in www_auth
    assert 'resource_metadata="http://16.112.106.229:8000/.well-known/oauth-protected-resource"' in www_auth
    assert 'error="invalid_token"' in www_auth
    print("PASS: test_unauthenticated_request_rejected")


def test_invalid_token_rejected():
    """Verify request with invalid/forged Bearer token is rejected with 401."""
    app = mcp.sse_app()
    client = TestClient(app)

    res = client.get("/sse", headers={"Authorization": "Bearer bogus_token_12345"})
    assert res.status_code == 401
    assert "www-authenticate" in res.headers
    print("PASS: test_invalid_token_rejected")


def test_insufficient_scope_rejected():
    """Verify token missing required scope returns 403 Forbidden."""
    # Generate an unverified token with wrong scope
    token_payload = {
        "aud": "47722668-aafe-422a-a167-10c32d67c2f0",
        "iss": "https://login.microsoftonline.com/organizations/v2.0",
        "sub": "test-user-id",
        "scp": "other:scope",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    unverified_token = jwt.encode(token_payload, "test-secret", algorithm="HS256")

    app = mcp.sse_app()
    client = TestClient(app)

    res = client.get("/sse", headers={"Authorization": f"Bearer {unverified_token}"})
    # FastMCP RequireAuthMiddleware rejects with 403 when scope is missing
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    assert "insufficient_scope" in res.headers.get("www-authenticate", "")
    print("PASS: test_insufficient_scope_rejected")


def test_valid_token_accepted():
    """Verify token with required scope (mcp:tools) is accepted."""
    token_payload = {
        "aud": "47722668-aafe-422a-a167-10c32d67c2f0",
        "iss": "https://login.microsoftonline.com/organizations/v2.0",
        "sub": "subbu@vithiit.com",
        "preferred_username": "subbu@vithiit.com",
        "scp": "mcp:tools User.Read",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    valid_token = jwt.encode(token_payload, "test-secret", algorithm="HS256")

    app = mcp.sse_app()
    client = TestClient(app, base_url="http://localhost:8000")

    # POST to /messages with valid token should pass auth and reach message handler (which returns 400 for unknown session)
    res = client.post(
        "/messages/?session_id=nonexistent",
        headers={"Authorization": f"Bearer {valid_token}"},
        json={"jsonrpc": "2.0", "id": 1, "method": "ping"}
    )
    # Status should NOT be 401 or 403 — auth succeeded!
    assert res.status_code != 401, f"Expected authenticated, got 401: {res.text}"
    assert res.status_code != 403, f"Expected scope satisfied, got 403: {res.text}"
    # Unknown session returns 404 or 400
    assert res.status_code in (400, 404), f"Expected 400/404 from message handler, got {res.status_code}"
    print(f"PASS: test_valid_token_accepted (Auth passed, reached handler with status {res.status_code})")


if __name__ == "__main__":
    test_protected_resource_metadata()
    test_unauthenticated_request_rejected()
    test_invalid_token_rejected()
    test_insufficient_scope_rejected()
    test_valid_token_accepted()
    print("\nALL 5 TESTS PASSED SUCCESSFULLY! [OK]")
