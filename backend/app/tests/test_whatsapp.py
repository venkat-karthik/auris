# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
import httpx

from app.models.agent import Agent
from app.models.whatsapp_number import WhatsappNumber
from app.models.call_run import CallRun

@pytest.mark.asyncio
async def test_whatsapp_crud_endpoints(client, db_session, test_org, test_user, override_auth, auth_headers):
    # Create agent first
    agent = Agent(
        org_id=test_org.id,
        created_by=test_user.id,
        name="Support Agent",
        model_config={"system_prompt": "You are a customer assistant."}
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    # 1. Add WhatsApp number
    response = await client.post(
        "/whatsapp",
        json={"phone_number": "+1234567890", "label": "Support Desk"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone_number"] == "+1234567890"
    assert data["label"] == "Support Desk"
    assert data["agent_id"] is None
    number_id = data["id"]

    # 2. List WhatsApp numbers
    response = await client.get("/whatsapp", headers=auth_headers)
    assert response.status_code == 200
    numbers = response.json()
    assert len(numbers) == 1
    assert numbers[0]["phone_number"] == "+1234567890"

    # 3. Bind agent
    response = await client.put(
        f"/whatsapp/{number_id}/bind",
        json={"agent_id": agent.id},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == agent.id
    assert data["agent_name"] == "Support Agent"

    # 4. Outbound messaging API
    with patch("app.routes.whatsapp.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        response = await client.post(
            f"/whatsapp/{number_id}/send",
            json={"to_number": "+1987654321", "message": "Hello from outbound!"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == {"message": "WhatsApp message sent successfully."}
        mock_send.assert_called_once_with("+1987654321", "Hello from outbound!")

        # Verify CallRun of transport='text' was created
        result = await db_session.execute(
            select(CallRun).where(CallRun.transport == "text")
        )
        run = result.scalar_one_or_none()
        assert run is not None
        assert run.caller_number == "+1987654321"
        assert run.called_number == "+1234567890"
        assert run.gathered_context["whatsapp_messages"][-1]["content"] == "Hello from outbound!"


@pytest.mark.asyncio
async def test_whatsapp_webhook_verification(client):
    response = await client.get(
        "/whatsapp/webhook?hub.mode=subscribe&hub.challenge=test_challenge&hub.verify_token=auris_whatsapp_verify_token"
    )
    assert response.status_code == 200
    assert response.text == "test_challenge"


@pytest.mark.asyncio
async def test_whatsapp_inbound_webhook(client, db_session, test_org, test_user):
    # Setup agent and register WhatsApp number
    agent = Agent(
        org_id=test_org.id,
        created_by=test_user.id,
        name="Support Agent",
        model_config={"system_prompt": "Always say 'Auris is awesome'"}
    )
    db_session.add(agent)
    await db_session.flush()

    num = WhatsappNumber(
        org_id=test_org.id,
        phone_number="+1234567890",
        label="Webhook Test Desk",
        is_active=True,
        agent_id=agent.id
    )
    db_session.add(num)
    await db_session.commit()

    # Payload simulation for WhatsApp Business API
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "12345",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+1234567890",
                                "phone_number_id": "98765"
                            },
                            "messages": [
                                {
                                    "from": "+15550009999",
                                    "type": "text",
                                    "text": {
                                        "body": "Help me reset password"
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    original_post = httpx.AsyncClient.post
    async def mock_post(self_obj, url, *args, **kwargs):
        if "openai.com" in str(url):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "To reset password, click the link."
                        }
                    }
                ]
            }
            return mock_response
        return await original_post(self_obj, url, *args, **kwargs)

    # Mock the LLM completion call and sending back to client
    with patch("app.core.config.OPENAI_API_KEY", "real-api-key-for-test"), \
         patch.object(httpx.AsyncClient, "post", new=mock_post), \
         patch("app.routes.whatsapp.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        
        mock_send.return_value = True

        response = await client.post("/whatsapp/webhook", json=webhook_payload)
        assert response.status_code == 200
        assert response.json() == {"status": "event_received"}

        # Verify message sent back to customer
        mock_send.assert_called_once_with("+15550009999", "To reset password, click the link.")

        # Verify database history logging
        result = await db_session.execute(
            select(CallRun).where(
                CallRun.transport == "text",
                CallRun.caller_number == "+15550009999"
            )
        )
        run = result.scalar_one_or_none()
        assert run is not None
        assert len(run.gathered_context["whatsapp_messages"]) == 2
        assert run.gathered_context["whatsapp_messages"][0]["role"] == "user"
        assert run.gathered_context["whatsapp_messages"][1]["role"] == "assistant"
        assert run.gathered_context["whatsapp_messages"][1]["content"] == "To reset password, click the link."
