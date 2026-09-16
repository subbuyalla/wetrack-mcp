# WeTrack Enterprise MCP Server 🚀

A **Python MCP (Model Context Protocol) Server** that exposes the entire WeTrack/VTrack
REST API as AI-callable tools — enabling Claude, Cursor, Gemini, and any MCP-compatible
AI assistant to manage projects, tickets, sprints, and more in natural language.

---

## ✅ What's Included

| Module | Tools | Coverage |
|---|---|---|
| 🔐 Auth | 7 | Sign-in, sign-out, password, impersonation |
| 🔑 OAuth | 3 | Microsoft sign-in URL, token setter, callback info |
| 🎫 Tickets | 13 | EPIC/STORY/TASK/BUG + support tickets, comments, history |
| 📁 Projects | 17 | CRUD + overview, reports, team, files, folders |
| 🏃 Sprints | 5 | Full sprint lifecycle management |
| 👤 Users | 7 | Create (single/bulk), update, invite management |
| 🏢 Clients | 7 | Client orgs, organisations, member assignment |
| 📊 Dashboard | 1 | Aggregated KPIs and analytics |
| 📈 Reports | 11 | Unified reports, My Work, My Sprint, widget CRUD |
| 🔔 Notifications | 4 | Feed, unread count, mark read |
| 🔍 Search | 1 | Global search across all entities |
| 🗂️ Master Data | 17 | Statuses, priorities, categories, types, products, timezones |
| 🧩 Metadata | 6 | Custom field definitions |
| 📤 Uploads | 2 | S3 presigned URLs, upload instructions |
| ⚡ Webhooks & Cron | 3 | SLA check trigger, sprint burndown snapshot, email webhook info |
| **Total** | **110** | **Complete WeTrack Enterprise API coverage** |

---

## 🛠️ Requirements

- **Python 3.11+**
- **uv** (recommended) or pip

---

## 🚀 Quick Start

### 1. Install uv (if not already installed)
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Set up credentials
```bash
# Copy the template
copy .env.example .env    # Windows
cp .env.example .env       # macOS/Linux

# Edit .env and fill in your WeTrack credentials:
# WETRACK_BASE_URL=https://wetrack-two.vercel.app
# WETRACK_EMAIL=your@email.com
# WETRACK_PASSWORD=YourPassword123
```

### 3. Install dependencies
```bash
uv sync
```

### 4. Run the MCP server
```bash
# stdio mode (for Claude Desktop / Cursor)
uv run python -m wetrack_mcp.server

# SSE mode (for HTTP/web clients)
MCP_TRANSPORT=sse uv run python -m wetrack_mcp.server
```

---

## 🐳 Docker & EC2 Deployment

### 1. Run with Docker Compose (Recommended for EC2)

```bash
# Clone the repository
git clone https://github.com/subbuyalla/wetrack-mcp.git
cd wetrack-mcp

# Create .env from template and configure credentials
cp .env.example .env
nano .env

# Build and start in background
docker compose up -d --build
```

### 2. Check Container Logs & Health

```bash
# Check running status
docker compose ps

# View live logs
docker compose logs -f
```

The MCP SSE server listens on port `8000`:
* SSE URL: `http://<YOUR_EC2_PUBLIC_IP>:8000/sse`
* Message endpoint: `http://<YOUR_EC2_PUBLIC_IP>:8000/messages/`

> **Note for EC2 Security Groups:** Ensure your AWS EC2 Security Group allows inbound TCP traffic on port `8000` (or place behind Nginx/ALB on port 443 with SSL).

---

## 🔌 Connecting to Any AI Platform

The WeTrack MCP server is universal and connects to all major AI assistants and IDEs:

### 1. Claude Desktop

#### Option A: Connect to Cloud EC2 Deployment (Zero local setup for teammates)
Open `%APPDATA%\Claude\claude_desktop_config.json` (or click **Settings → Developer → Edit config**):
```json
{
  "mcpServers": {
    "wetrack": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://<YOUR_EC2_PUBLIC_IP>:8000/sse",
        "--allow-http"
      ]
    }
  }
}
```

#### Option B: Run Locally on your computer (stdio)
```json
{
  "mcpServers": {
    "wetrack": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/wetrack-mcp",
        "python",
        "-m",
        "wetrack_mcp.server"
      ],
      "env": {
        "WETRACK_BASE_URL": "https://wetrack-two.vercel.app",
        "WETRACK_EMAIL": "your@email.com",
        "WETRACK_PASSWORD": "yourpassword"
      }
    }
  }
}
```
*Restart Claude Desktop after saving.*

---

### 2. Cursor IDE

Cursor supports native remote SSE connections with zero Node.js or local installation required:

1. Open **Cursor Settings** (`Ctrl + Shift + J` or `Cmd + Shift + J`) → **MCP**.
2. Click **+ Add New MCP Server**.
3. Fill in:
   * **Name:** `wetrack`
   * **Type:** `sse`
   * **URL:** `http://<YOUR_EC2_PUBLIC_IP>:8000/sse`
4. Click **Add**. All 110 tools will instantly show green in Composer!

---

### 3. VS Code (Cline / Roo Code / Continue)

In your extension's MCP configuration settings (`cline_mcp_settings.json` or `config.json`):

```json
{
  "mcpServers": {
    "wetrack": {
      "url": "http://<YOUR_EC2_PUBLIC_IP>:8000/sse",
      "transport": "sse"
    }
  }
}
```

---

### 4. Windsurf (Codeium)

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "wetrack": {
      "serverUrl": "http://<YOUR_EC2_PUBLIC_IP>:8000/sse"
    }
  }
}
```

---

### 5. ChatGPT

#### Method A: Custom GPT Action (Easiest & Most Popular)
1. In ChatGPT, click **Explore GPTs → + Create**.
2. Go to the **Configure** tab → scroll down and click **Create new action**.
3. Import or paste the schema from [`chatgpt-actions-schema.yaml`](./chatgpt-actions-schema.yaml).
4. Configure Authentication (Bearer token or session cookie).
5. Save the GPT — you can now manage WeTrack tickets and projects directly in ChatGPT web or mobile!

#### Method B: ChatGPT Developer Mode (MCP)
1. Open ChatGPT **Settings → Developer Mode / Connectors**.
2. Select **Add MCP Server** and enter your EC2 HTTPS URL.

---

### 6. Python & LangChain AI Agents

Integrate WeTrack tools directly into custom LangChain / LangGraph workflows:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

async with MultiServerMCPClient(
    {"wetrack": {"url": "http://<YOUR_EC2_PUBLIC_IP>:8000/sse", "transport": "sse"}}
) as client:
    tools = client.get_tools()
    agent = create_react_agent(model, tools)
    response = await agent.ainvoke({"messages": "List open tickets in WeTrack"})
```

---

## 🔐 Authentication

Authentication is **fully automatic**:
1. The server reads `WETRACK_EMAIL` and `WETRACK_PASSWORD` from `.env`
2. On the first tool call, it auto-logs in and stores the JWT token
3. On `401 Unauthorized`, it automatically re-logs in and retries
4. You can also call `wetrack_sign_in` manually from the AI chat

**Example prompts after setup:**
```
"Show me all open tickets in the WeTrack Platform project"
"Create a TASK titled 'Fix login page bug' in the WTP project with High priority"
"What sprints are currently in progress?"
"List all users in the organisation"
```

---

## 📁 Project Structure

```
wetrack-mcp/
├── src/wetrack_mcp/
│   ├── server.py           ← Entry point
│   ├── auth.py             ← JWT token management
│   ├── client.py           ← HTTP client with auto-auth
│   ├── config.py           ← Environment config
│   └── tools/
│       ├── auth_tools.py
│       ├── ticket_tools.py
│       ├── project_tools.py
│       ├── sprint_tools.py
│       ├── user_tools.py
│       ├── client_tools.py
│       ├── dashboard_tools.py
│       ├── report_tools.py
│       ├── notification_tools.py
│       ├── search_tools.py
│       ├── master_tools.py
│       └── metadata_tools.py
├── .env.example
├── .env              ← Your credentials (gitignored)
└── pyproject.toml
```

---

## 🌐 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `WETRACK_BASE_URL` | Yes | API base URL (staging or production) |
| `WETRACK_EMAIL` | Yes* | Login email |
| `WETRACK_PASSWORD` | Yes* | Login password |
| `WETRACK_TOKEN` | No | Pre-set JWT token (skips auto-login) |
| `MCP_TRANSPORT` | No | `stdio` (default) or `sse` |
| `MCP_HOST` | No | SSE host (default: `0.0.0.0`) |
| `MCP_PORT` | No | SSE port (default: `8000`) |

*Required unless `WETRACK_TOKEN` is set.

---

## 🏭 Production Switch

When ready to go to production, just update `.env`:
```env
WETRACK_BASE_URL=https://your-production-url.com
```

No code changes needed.

---

## 🔄 Switching to TypeScript

Once testing is complete, the TypeScript port will use:
- `@modelcontextprotocol/sdk`
- `axios` for HTTP
- `zod` for validation

The tool names and behaviors will be identical.
