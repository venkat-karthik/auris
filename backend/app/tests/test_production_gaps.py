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
