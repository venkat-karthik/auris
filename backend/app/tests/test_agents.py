import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import Agent

@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org):
    payload = {
        "name": "Test Agent",
        "description": "Custom agent prompt",
        "graph": {"system_prompt": "Prompt..."},
        "model_config_data": {"stt": {"provider": "deepgram"}},
        "context_variables": {"name": "val"}
    }
    response = await client.post("/agents", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Agent"
    assert data["org_id"] == test_org.id
    assert data["model_config"]["stt"]["provider"] == "deepgram"
    
    # Check DB
    result = await db_session.execute(select(Agent).where(Agent.id == data["id"]))
    agent = result.scalar_one_or_none()
    assert agent is not None
    assert agent.name == "Test Agent"
    assert agent.description == "Custom agent prompt"

@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org, test_user):
    agent1 = Agent(org_id=test_org.id, created_by=test_user.id, name="Agent 1")
    agent2 = Agent(org_id=test_org.id, created_by=test_user.id, name="Agent 2")
    db_session.add_all([agent1, agent2])
    await db_session.commit()

    response = await client.get("/agents", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    names = [a["name"] for a in data]
    assert "Agent 1" in names
    assert "Agent 2" in names

@pytest.mark.asyncio
async def test_get_agent(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org, test_user):
    agent = Agent(org_id=test_org.id, created_by=test_user.id, name="Specific Agent")
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    response = await client.get(f"/agents/{agent.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Specific Agent"

@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org, test_user):
    agent = Agent(org_id=test_org.id, created_by=test_user.id, name="Old Name")
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    payload = {"name": "New Name"}
    response = await client.put(f"/agents/{agent.id}", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"

    # Verify DB update
    await db_session.refresh(agent)
    assert agent.name == "New Name"

@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org, test_user):
    agent = Agent(org_id=test_org.id, created_by=test_user.id, name="To Delete")
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    response = await client.delete(f"/agents/{agent.id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify soft delete
    await db_session.refresh(agent)
    assert agent.is_active is False
