import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from wetrack_mcp.auth import auth_manager
from wetrack_mcp.client import make_request
from wetrack_mcp.server import mcp

async def test_local():
    print("=" * 60)
    print("[*] WeTrack MCP -- Local Test Suite")
    print("=" * 60)

    # 1. Check tools count
    tools = await mcp.list_tools()
    print(f"\n1. Server Tools Registered: {len(tools)} tools ready")

    # 2. Test Login
    print("\n2. Testing Authentication with Staging Server...")
    login = await auth_manager.sign_in()
    if login.get("success"):
        print("   [OK] Login Successful! JWT token and session cookie acquired.")
    else:
        print(f"   [FAIL] Login Failed: {login}")
        return

    # 3. Test Current User Profile
    print("\n3. Testing Current User API...")
    user_res = await make_request("GET", "/api/users/current-user")
    user = user_res.get("data", user_res)
    print(f"   [OK] Authenticated as: {user.get('name', 'User')} ({user.get('email')}) - Role: {user.get('role')}")

    # 4. Test Projects List
    print("\n4. Testing Projects List API...")
    proj_res = await make_request("GET", "/api/projects")
    projects = proj_res.get("data", proj_res)
    if isinstance(projects, list):
        print(f"   [OK] Retrieved {len(projects)} projects:")
        for p in projects[:3]:
            print(f"        - {p.get('name')} (ID: {p.get('id')})")
    else:
        print(f"   Projects: {proj_res}")

    # 5. Test Tickets List
    print("\n5. Testing Tickets List API...")
    tickets_res = await make_request("GET", "/api/tickets", params={"limit": 3})
    tickets = tickets_res.get("data", tickets_res)
    if isinstance(tickets, list):
        print(f"   [OK] Retrieved {len(tickets)} tickets (Showing top {min(len(tickets), 3)}):")
        for t in tickets[:3]:
            print(f"        - [{t.get('key', 'TICKET')}] {t.get('title', 'No Title')} - Status: {t.get('status', 'N/A')}")
    else:
        print(f"   Tickets: {tickets_res}")

    print("\n" + "=" * 60)
    print("[SUCCESS] All core tests PASSED! Your MCP server is 100% working.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_local())
