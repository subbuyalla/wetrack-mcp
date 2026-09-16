# Multi-stage Dockerfile for WeTrack Enterprise MCP Server
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    MCP_TRANSPORT=sse \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

WORKDIR /app

# Install curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY pyproject.toml README.md ./

# Install dependencies and project package
RUN pip install --no-cache-dir .

# Copy application source code
COPY src/ ./src/

# Expose MCP SSE port
EXPOSE 8000

# Health check (uses python urllib to check HTTP 200 without hanging on SSE stream)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; resp = urllib.request.urlopen('http://127.0.0.1:8000/sse', timeout=3); exit(0 if resp.status == 200 else 1)" || exit 1

# Start the MCP server
CMD ["python", "-m", "wetrack_mcp.server"]
