import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import Agent

@pytest.mark.asyncio
async def test_get_mcp_manifest(client: AsyncClient):
    response = await client.get("/mcp")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Auris Voice AI MCP Server"
    assert data["version"] == "1.0.0"
    assert "tools" in data
    assert "resources" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "dispatch_call" in tool_names
    assert "create_agent" in tool_names
    assert "get_balance" in tool_names

@pytest.mark.asyncio
async def test_mcp_tool_get_balance(client: AsyncClient, auth_headers):
    payload = {"name": "get_balance"}
    response = await client.post("/mcp/tools/call", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["tool"] == "get_balance"
    assert "balance_credits" in data["result"]

@pytest.mark.asyncio
async def test_mcp_tool_create_agent(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org):
    payload = {
        "name": "create_agent",
        "arguments": {
            "name": "MCP Created Agent",
            "system_prompt": "You are a test voice agent created via MCP.",
            "welcome_message": "Hello from MCP!"
        }
    }
    response = await client.post("/mcp/tools/call", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["tool"] == "create_agent"
    assert data["result"]["name"] == "MCP Created Agent"
    
    agent_id = data["result"]["agent_id"]
    res = await db_session.execute(select(Agent).where(Agent.id == agent_id))
    agent = res.scalar_one_or_none()
    assert agent is not None
    assert agent.name == "MCP Created Agent"
    assert agent.org_id == test_org.id

@pytest.mark.asyncio
async def test_mcp_list_resources(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org, test_user):
    # Add an agent
    agent = Agent(org_id=test_org.id, created_by=test_user.id, name="Resource Agent", is_active=True)
    db_session.add(agent)
    await db_session.commit()

    response = await client.get("/mcp/resources?uri=agents://all", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["uri"] == "agents://all"
    names = [a["name"] for a in data["data"]]
    assert "Resource Agent" in names

    # Add a call run to test calls://recent
    from app.models.call_run import CallRun
    call_run = CallRun(
        org_id=test_org.id,
        agent_id=agent.id,
        transport="telnyx",
        call_type="outbound",
        status="initiated",
    )
    db_session.add(call_run)
    await db_session.commit()

    response = await client.get("/mcp/resources?uri=calls://recent", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["uri"] == "calls://recent"
    assert len(data["data"]) == 1
    assert data["data"][0]["direction"] == "outbound"


@pytest.mark.asyncio
async def test_mcp_tool_dispatch_call(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org, test_user):
    agent = Agent(org_id=test_org.id, created_by=test_user.id, name="Dispatch Agent", is_active=True)
    db_session.add(agent)
    await db_session.commit()

    payload = {
        "name": "dispatch_call",
        "arguments": {
            "agent_id": agent.id,
            "to_number": "+15551234567",
            "call_context": {"user_name": "Alice"}
        }
    }
    response = await client.post("/mcp/tools/call", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["to_number"] == "+15551234567"
    assert data["result"]["status"] == "initiated"


@pytest.mark.asyncio
async def test_mcp_invalid_tool(client: AsyncClient, auth_headers):
    payload = {"name": "unknown_tool_call"}
    response = await client.post("/mcp/tools/call", json=payload, headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Tool 'unknown_tool_call' not found"
