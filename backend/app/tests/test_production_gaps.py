import pytest
import struct
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pipeline.frame import Frame, FrameType
from app.services.pipeline.stt.vad import VADProcessor
from app.services.pipeline.llm.openai_llm import OpenAILLM
from app.models.organization import Organization


@pytest.mark.asyncio
async def test_vad_onset_offset_detection():
    # 1. Initialize processor with low silence limit for rapid testing
    processor = VADProcessor(threshold=100.0, silence_limit_ms=100.0, onset_limit_ms=20.0)
    
    emitted_frames = []
    async def mock_emit(frame):
        emitted_frames.append(frame)
    processor.emit = mock_emit

    # Generate a loud sound frame (PCM 16-bit Mono, 16000Hz, size 640 bytes = 20ms chunk)
    loud_data = struct.pack("<320h", *[500] * 320)
    loud_frame = Frame(type=FrameType.AUDIO_IN, data=loud_data)

    # Process loud frames to trigger voice onset (USER_SPEAKING)
    await processor.process_frame(loud_frame)
    await processor.process_frame(loud_frame)
    
    assert any(f.type == FrameType.USER_SPEAKING for f in emitted_frames)
    
    # Reset list and process silent frames (all zeros)
    emitted_frames.clear()
    silent_data = struct.pack("<320h", *[0] * 320)
    silent_frame = Frame(type=FrameType.AUDIO_IN, data=silent_data)

    # Send 120ms of silence (6 frames of 20ms) to trigger voice offset (USER_SILENT)
    for _ in range(6):
        await processor.process_frame(silent_frame)
        
    assert any(f.type == FrameType.USER_SILENT for f in emitted_frames)


@pytest.mark.asyncio
async def test_openai_llm_interruption():
    # Initialize LLM processor
    llm = OpenAILLM(api_key="mock-key")
    
    # Mock a running background generate task
    mock_task = MagicMock()
    mock_task.done.return_value = False
    llm._gen_task = mock_task

    # Send USER_SPEAKING frame to trigger interruption
    await llm.process_frame(Frame(type=FrameType.USER_SPEAKING))
    
    # Verify task was canceled
    mock_task.cancel.assert_called_once()


@pytest.mark.asyncio
async def test_settings_org_and_keys_endpoints(client: AsyncClient, db_session: AsyncSession, test_org, test_user):
    with (
        patch("app.dependencies.auth.get_current_org", return_value=test_org),
        patch("app.dependencies.auth.get_current_user", return_value=test_user)
    ):
        # 1. Update organization name
        org_payload = {"name": "Auris Enterprise Team"}
        response = await client.put("/api/v1/auth/organization", json=org_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Auris Enterprise Team"

        # 2. Create API key
        key_payload = {"name": "Prod Server"}
        key_resp = await client.post("/api/v1/api-keys", json=key_payload)
        assert key_resp.status_code == 201
        key_data = key_resp.json()
        assert key_data["name"] == "Prod Server"
        assert "raw_key" in key_data
        assert key_data["raw_key"].startswith("ak_")
        key_id = key_data["id"]

        # 3. List API keys
        list_resp = await client.get("/api/v1/api-keys")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert len(list_data) >= 1
        assert list_data[0]["key_prefix"] == key_data["key_prefix"]

        # 4. Revoke API key
        delete_resp = await client.delete(f"/api/v1/api-keys/{key_id}")
        assert delete_resp.status_code == 200

        # Verify key list is now empty (archived keys filtered out)
        list_resp2 = await client.get("/api/v1/api-keys")
        assert len(list_resp2.json()) == 0


@pytest.mark.asyncio
async def test_email_verification_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Sign up user
    signup_payload = {
        "email": "test-verify@domain.com",
        "password": "securepassword123",
        "full_name": "Verify Tester",
        "org_name": "Verification Corp"
    }
    response = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test-verify@domain.com"
    assert data["is_verified"] is False

    # Get user code directly from database
    from app.models.user import User
    from sqlalchemy import select
    res = await db_session.execute(select(User).where(User.email == "test-verify@domain.com"))
    user = res.scalar_one_or_none()
    assert user is not None
    assert user.verification_code is not None

    # 2. Try logging in before verifying (should fail with 403)
    login_payload = {
        "email": "test-verify@domain.com",
        "password": "securepassword123"
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 403
    assert "verify" in login_resp.json()["detail"].lower()

    # 3. Call verify with wrong code (should fail)
    verify_payload_wrong = {
        "email": "test-verify@domain.com",
        "code": "000000"
    }
    verify_resp_wrong = await client.post("/api/v1/auth/verify", json=verify_payload_wrong)
    assert verify_resp_wrong.status_code == 400

    # 4. Verify with correct code (should succeed and return token)
    verify_payload_correct = {
        "email": "test-verify@domain.com",
        "code": user.verification_code
    }
    verify_resp_correct = await client.post("/api/v1/auth/verify", json=verify_payload_correct)
    assert verify_resp_correct.status_code == 200
    token_data = verify_resp_correct.json()
    assert "access_token" in token_data
    assert token_data["user_id"] == user.id

    # 5. Log in after verifying (should succeed)
    login_resp2 = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp2.status_code == 200
    assert "access_token" in login_resp2.json()


@pytest.mark.asyncio
async def test_phone_number_leasing_and_binding(client: AsyncClient, db_session: AsyncSession, test_org, test_user):
    with (
        patch("app.dependencies.auth.get_current_org", return_value=test_org),
        patch("app.dependencies.auth.get_current_user", return_value=test_user)
    ):
        # Set org balance to have enough credits
        test_org.balance_credits = 500.0
        await db_session.commit()

        # 1. Search available numbers
        search_resp = await client.get("/api/v1/phone-numbers/search?area_code=830")
        assert search_resp.status_code == 200
        available = search_resp.json()
        assert len(available) >= 1
        phone_to_buy = available[0]["phone_number"]

        # 2. Buy/lease the number
        buy_payload = {"phone_number": phone_to_buy, "label": "Support Desk Line"}
        buy_resp = await client.post("/api/v1/phone-numbers/buy", json=buy_payload)
        assert buy_resp.status_code == 200
        bought_data = buy_resp.json()
        assert bought_data["phone_number"] == phone_to_buy
        assert bought_data["label"] == "Support Desk Line"
        number_id = bought_data["id"]

        # Org balance should be reduced (500 - 160 = 340)
        assert test_org.balance_credits == 340.0

        # 3. List leased numbers
        list_resp = await client.get("/api/v1/phone-numbers")
        assert list_resp.status_code == 200
        numbers = list_resp.json()
        assert any(n["id"] == number_id for n in numbers)

        # 4. Bind number to agent
        # Create a dummy agent first
        from app.models.agent import Agent
        dummy_agent = Agent(org_id=test_org.id, name="Telnyx Inbound Assistant")
        db_session.add(dummy_agent)
        await db_session.commit()

        bind_payload = {"agent_id": dummy_agent.id}
        bind_resp = await client.put(f"/api/v1/phone-numbers/{number_id}/bind", json=bind_payload)
        assert bind_resp.status_code == 200
        bound_data = bind_resp.json()
        assert bound_data["agent_id"] == dummy_agent.id
        assert bound_data["agent_name"] == "Telnyx Inbound Assistant"

        # 5. Release number
        del_resp = await client.delete(f"/api/v1/phone-numbers/{number_id}")
        assert del_resp.status_code == 200

        # Verify number list is empty again
        list_resp2 = await client.get("/api/v1/phone-numbers")
        assert len(list_resp2.json()) == 0
