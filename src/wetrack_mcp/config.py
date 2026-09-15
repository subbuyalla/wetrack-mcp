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


config = Config()
