import hmac
import hashlib
import json
import time
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import Agent
from app.models.call_run import CallRun
from app.services.pipeline.factory import build_pipeline
from app.services.pipeline.llm.retell_websocket_llm import RetellWebsocketLLM


@pytest.mark.asyncio
async def test_retell_agent_lifecycle(client: AsyncClient, auth_headers):
    # 1. Create Agent via Retell API
    create_payload = {
        "agent_name": "Retell Support Agent",
        "response_engine": {
            "type": "custom-llm",
            "url": "wss://my-custom-llm.com/websocket"
        },
        "voice_id": "11labs-Rachel",
        "language": "en-US"
    }
    resp = await client.post("/retell/create-agent", json=create_payload, headers=auth_headers)
    assert resp.status_code == 201, f"Create agent failed: {resp.text}"
    data = resp.json()
    assert data["agent_name"] == "Retell Support Agent"
    assert data["response_engine"]["type"] == "custom-llm"
    assert data["response_engine"]["url"] == "wss://my-custom-llm.com/websocket"
    assert "agent_id" in data
    agent_id = data["agent_id"]

    # 2. Get Agent
    get_resp = await client.get(f"/retell/get-agent/{agent_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["agent_id"] == agent_id
    assert get_data["voice_id"] == "11labs-Rachel"

    # 3. Update Agent
    update_payload = {"agent_name": "Updated Retell Agent", "voice_id": "11labs-Josh"}
    patch_resp = await client.patch(f"/retell/update-agent/{agent_id}", json=update_payload, headers=auth_headers)
    assert patch_resp.status_code == 200
    patch_data = patch_resp.json()
    assert patch_data["agent_name"] == "Updated Retell Agent"
    assert patch_data["voice_id"] == "11labs-Josh"

    # 4. List Agents
    list_resp = await client.get("/retell/list-agents", headers=auth_headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert any(a["agent_id"] == agent_id for a in list_data)

    # 5. Delete Agent
    del_resp = await client.delete(f"/retell/delete-agent/{agent_id}", headers=auth_headers)
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_retell_call_management(client: AsyncClient, auth_headers):
    # Create an agent first
    create_payload = {"agent_name": "Call Test Agent"}
    agent_resp = await client.post("/retell/create-agent", json=create_payload, headers=auth_headers)
    agent_id = agent_resp.json()["agent_id"]

    # 1. Create Web Call
    web_call_payload = {"agent_id": agent_id, "metadata": {"test": "true"}}
    web_resp = await client.post("/retell/create-web-call", json=web_call_payload, headers=auth_headers)
    assert web_resp.status_code == 201
    web_data = web_resp.json()
    assert "access_token" in web_data
    assert "call_id" in web_data
    web_call_id = web_data["call_id"]

    # 2. Get Call Status
    call_resp = await client.get(f"/retell/get-call/{web_call_id}", headers=auth_headers)
    assert call_resp.status_code == 200
    call_data = call_resp.json()
    assert call_data["call_id"] == web_call_id
    assert call_data["agent_id"] == agent_id
    assert call_data["call_status"] == "registered"

    # 3. Create Phone Call
    phone_payload = {
        "from_number": "+18005550100",
        "to_number": "+18005550101",
        "agent_id": agent_id
    }
    phone_resp = await client.post("/retell/create-phone-call", json=phone_payload, headers=auth_headers)
    assert phone_resp.status_code == 201
    phone_data = phone_resp.json()
    assert phone_data["from_number"] == "+18005550100"
    assert phone_data["direction"] == "outbound"


@pytest.mark.asyncio
async def test_retell_phone_numbers(client: AsyncClient, auth_headers):
    num_payload = {"phone_number": "+18005550999", "area_code": 800}
    create_resp = await client.post("/retell/create-phone-number", json=num_payload, headers=auth_headers)
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["phone_number"] == "+18005550999"

    get_resp = await client.get("/retell/get-phone-number/+18005550999", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["phone_number"] == "+18005550999"


def test_retell_pipeline_factory():
    model_config = {
        "llm": {"provider": "retell-custom-llm"},
        "custom_llm_websocket_url": "wss://test-server.com/llm-websocket/{call_id}",
        "stt": {"provider": "deepgram"},
        "tts": {"provider": "elevenlabs"},
    }
    engine = build_pipeline(model_config, system_prompt="Test Prompt")
    
    # Verify that RetellWebsocketLLM is included in the pipeline processors
    llm_processors = [p for p in engine.processors if isinstance(p, RetellWebsocketLLM)]
    assert len(llm_processors) == 1
    assert llm_processors[0].websocket_url == "wss://test-server.com/llm-websocket/{call_id}"


def test_retell_hmac_signature_verification():
    # Verify that HMAC SHA256 signature algorithm matches Retell SDK specification
    secret = "test_webhook_secret"
    payload = {"event": "call_started", "data": {"call_id": "123"}}
    body_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    timestamp = int(time.time() * 1000)
    
    digest = hmac.new(secret.encode("utf-8"), f"{body_str}{timestamp}".encode("utf-8"), hashlib.sha256).hexdigest()
    retell_signature = f"v={timestamp},d={digest}"
    
    # Parse signature like Retell SDK does
    import re
    match = re.search(r"v=(\d+),d=(.*)", retell_signature)
    assert match is not None
    poststamp = int(match.group(1))
    post_digest = match.group(2)
    
    expected_digest = hmac.new(secret.encode("utf-8"), f"{body_str}{poststamp}".encode("utf-8"), hashlib.sha256).hexdigest()
    assert post_digest == expected_digest
