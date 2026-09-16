"""Configuration — loads environment variables for WeTrack MCP."""

import os
from dotenv import load_dotenv

# Load .env from project root (works cross-platform)
load_dotenv()


class Config:
    BASE_URL: str = os.getenv("WETRACK_BASE_URL", "https://wetrack-two.vercel.app").rstrip("/")
    EMAIL: str = os.getenv("WETRACK_EMAIL", "")
    PASSWORD: str = os.getenv("WETRACK_PASSWORD", "")
    TOKEN: str = os.getenv("WETRACK_TOKEN", "")       # optional pre-set token
    AUTH_KEY: str = os.getenv("WETRACK_AUTH_KEY", "")  # system key for cron/SLA endpoints
    MCP_TRANSPORT: str = os.getenv("MCP_TRANSPORT", "stdio")
    MCP_HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT: int = int(os.getenv("MCP_PORT", "8000"))
    # OAuth 2.1 Server-Side Auth (Layer 1 security for SSE / Streamable HTTP)
    OAUTH_ENABLED: bool = os.getenv("OAUTH_ENABLED", "true" if os.getenv("MCP_TRANSPORT") in ("sse", "streamable-http") else "false").lower() in ("true", "1", "yes")
    OAUTH_ISSUER_URL: str = os.getenv(
        "OAUTH_ISSUER_URL",
        "https://login.microsoftonline.com/9f1b09f9-3d22-48d9-b96c-8f145c22df61/v2.0",
    ).rstrip("/")
    OAUTH_JWKS_URI: str = os.getenv(
        "OAUTH_JWKS_URI",
        "https://login.microsoftonline.com/9f1b09f9-3d22-48d9-b96c-8f145c22df61/discovery/v2.0/keys",
    )
    OAUTH_AUDIENCE: str = os.getenv("OAUTH_AUDIENCE", "47722668-aafe-422a-a167-10c32d67c2f0")
    
    @property
    def OAUTH_REQUIRED_SCOPES(self) -> list[str]:
        raw = os.getenv("OAUTH_REQUIRED_SCOPES", "mcp:tools")
        return [s.strip() for s in raw.split(",") if s.strip()]

    @property
    def RESOURCE_SERVER_URL(self) -> str:
        res = os.getenv("MCP_RESOURCE_SERVER_URL", "")
        if res:
            return res.rstrip("/")
        host = "localhost" if self.MCP_HOST in ("0.0.0.0", "127.0.0.1", "") else self.MCP_HOST
        return f"http://{host}:{self.MCP_PORT}"


config = Config()

