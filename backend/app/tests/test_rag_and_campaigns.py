import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.models.agent import Agent
from app.models.organization import Organization
from app.services.rag_service import chunk_text
from app.services.dialer_service import parse_csv_contacts
from app.services.pipeline.workflow_engine import WorkflowGraphEngine, WorkflowState


def test_chunk_text():
    text = "Hello world! This is a simple text to be chunked into parts."
    chunks = chunk_text(text, chunk_size=20, chunk_overlap=5)
    assert len(chunks) > 0
    assert chunks[0].startswith("Hello world!")


def test_parse_csv_contacts():
    csv_data = b"phone_number,name\n+919999999999,John Doe\n+918888888888,Jane Smith"
    contacts = parse_csv_contacts(csv_data)
    assert len(contacts) == 2
    assert contacts[0]["phone_number"] == "+919999999999"
    assert contacts[0]["name"] == "John Doe"


def test_visual_graph_engine_validation():
    # Valid linear graph
    valid_graph = {
        "nodes": [
            {"id": "start", "type": "startCall"},
            {"id": "agent_1", "type": "agent", "data": {"system_prompt": "Hello"}},
            {"id": "end", "type": "endCall"}
        ],
        "edges": [
            {"source": "start", "target": "agent_1"},
            {"source": "agent_1", "target": "end"}
        ]
    }
    success, err = WorkflowGraphEngine.validate_graph(valid_graph)
    assert success is True
    assert err is None

    # Invalid graph with cycles
    cyclic_graph = {
        "nodes": [
            {"id": "start", "type": "startCall"},
            {"id": "agent_1", "type": "agent"},
            {"id": "agent_2", "type": "agent"}
        ],
        "edges": [
            {"source": "start", "target": "agent_1"},
            {"source": "agent_1", "target": "agent_2"},
            {"source": "agent_2", "target": "agent_1"}  # Circular loop
        ]
    }
    success, err = WorkflowGraphEngine.validate_graph(cyclic_graph)
    assert success is False
    assert "circular" in err.lower()


@pytest.mark.asyncio
async def test_workflow_state_execution():
    graph = {
        "nodes": [
            {"id": "start", "type": "startCall"},
            {"id": "qa_1", "type": "qa", "data": {"question": "What is your age?", "expected_variable": "age"}},
            {"id": "end", "type": "endCall"}
        ],
        "edges": [
            {"source": "start", "target": "qa_1"},
            {"source": "qa_1", "target": "end"}
        ]
    }
    state = WorkflowState(graph, context_variables={"name": "Alice"})
    assert state.active_node_id == "start"
    
    # Executing start node should transition to first active node (qa_1)
    prompt, end_call = await state.execute_active_node()
    assert state.active_node_id == "qa_1"
    assert "What is your age?" in prompt
    assert end_call is False


@pytest.mark.asyncio
async def test_rag_upload_and_retrieve(client: AsyncClient, db_session: AsyncSession, test_org, test_user):
    # Authenticate header mocking is handled in conftest or we mock auth dependencies
    with (
        patch("app.dependencies.auth.get_current_org", return_value=test_org),
        patch("app.dependencies.auth.get_current_user", return_value=test_user),
        patch("app.routes.knowledge_base.upload_file_to_minio", return_value="minio-path"),
        patch("app.services.rag_service.generate_embeddings", return_value=[0.1] * 1536)
    ):
        files = {"file": ("test.txt", b"This is the document content to retrieve.", "text/plain")}
        response = await client.post("/api/v1/knowledge-base/upload", files=files)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test.txt"


@pytest.mark.asyncio
async def test_campaign_dialer_flow(client: AsyncClient, db_session: AsyncSession, test_org, test_user):
    # Setup dummy agent in DB
    agent = Agent(
        org_id=test_org.id,
        created_by=test_user.id,
        name="Campaign Agent",
        description="Outbound Dialer",
        model_config={}
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    with (
        patch("app.dependencies.auth.get_current_org", return_value=test_org),
        patch("app.dependencies.auth.get_current_user", return_value=test_user)
    ):
        # Create campaign
        campaign_payload = {"name": "Outbound Test", "agent_id": agent.id}
        response = await client.post("/api/v1/campaigns", json=campaign_payload)
        assert response.status_code == 201
        data = response.json()
        campaign_id = data["id"]
        assert data["name"] == "Outbound Test"

        # Upload CSV contacts list
        csv_file = {"file": ("numbers.csv", b"phone,name\n+917777777777,John", "text/csv")}
        upload_resp = await client.post(f"/api/v1/campaigns/{campaign_id}/contacts/upload", files=csv_file)
        assert upload_resp.status_code == 200

        # Verify stats
        stats_resp = await client.get(f"/api/v1/campaigns/{campaign_id}/stats")
        assert stats_resp.status_code == 200
        stats_data = stats_resp.json()
        assert stats_data["total_contacts"] == 1
        assert stats_data["pending"] == 1
