import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.whatsapp_number import WhatsappNumber
from app.models.integration import Integration
from app.models.cloned_voice import ClonedVoice
from app.models.reseller_query import ResellerQuery
from app.models.agent import Agent


@pytest.mark.asyncio
async def test_whatsapp_endpoints(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org, test_user):
    # 1. Add whatsapp number
    payload = {"phone_number": "+918309827125", "label": "Office Desk"}
    response = await client.post("/whatsapp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["phone_number"] == "+918309827125"
    assert data["label"] == "Office Desk"

    # 2. List whatsapp numbers
    list_res = await client.get("/whatsapp", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Create Agent and Bind it
    agent = Agent(org_id=test_org.id, created_by=test_user.id, name="Whatsapp Agent")
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    bind_payload = {"agent_id": agent.id}
    bind_res = await client.put(f"/whatsapp/{data['id']}/bind", json=bind_payload, headers=auth_headers)
    assert bind_res.status_code == 200
    assert bind_res.json()["agent_id"] == agent.id

    # 4. Delete whatsapp number
    del_res = await client.delete(f"/whatsapp/{data['id']}", headers=auth_headers)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_integrations_endpoints(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org):
    # 1. Connect integration
    payload = {"service_name": "cal.com", "is_connected": True}
    response = await client.post("/integrations/toggle", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["service_name"] == "cal.com"
    assert data["is_connected"] is True

    # 2. Get list of integrations
    list_res = await client.get("/integrations", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(x["service_name"] == "cal.com" for x in list_res.json())


@pytest.mark.asyncio
async def test_cloned_voices_endpoints(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org):
    # 1. Upload mock voice file
    files = {"file": ("recording.wav", b"mock-wave-audio-content-bytes-sample-long-enough" * 50, "audio/wav")}
    data = {"name": "My Custom Voice"}
    response = await client.post("/cloned-voices/upload", data=data, files=files, headers=auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["name"] == "My Custom Voice"
    assert "voice_id_" in res_data["voice_id"]

    # 2. List voices
    list_res = await client.get("/cloned-voices", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(v["name"] == "My Custom Voice" for v in list_res.json())


@pytest.mark.asyncio
async def test_reseller_endpoints(client: AsyncClient):
    # Submit inquiry
    payload = {
        "name": "Karthik Reseller",
        "email": "reseller@sales.com",
        "phone": "+919900000000",
        "volume": "10k - 50k mins",
        "interest": "subaccounts",
        "use_case": "Set up bulk campaigns channels."
    }
    response = await client.post("/reseller", json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == "reseller@sales.com"
