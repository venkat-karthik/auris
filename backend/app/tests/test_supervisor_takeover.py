import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

from app.services.pipeline.frame import Frame, FrameType
from app.services.pipeline.transport.webrtc_transport import WebRTCTransport


@pytest.mark.asyncio
async def test_supervisor_whisper_route(client: AsyncClient):
    """
    Test that whispering a coaching instruction publishes to the Redis coaching channel.
    """
    payload = {
        "call_run_id": 456,
        "instruction": "Ask about his budget."
    }
    with patch("app.routes.supervisor.redis_client") as mock_redis:
        mock_redis.publish = AsyncMock()
        response = await client.post("/supervisor/whisper", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_redis.publish.assert_called_once_with(
            "call:coaching:456",
            json.dumps({"instruction": "Ask about his budget."})
        )


@pytest.mark.asyncio
async def test_supervisor_takeover_start_stop(client: AsyncClient):
    """
    Test starting and stopping takeover mode sets/deletes the Redis key and publishes events.
    """
    payload = {"call_run_id": 456}
    with patch("app.routes.supervisor.redis_client") as mock_redis:
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()
        mock_redis.publish = AsyncMock()

        # Start takeover
        res_start = await client.post("/supervisor/takeover/start", json=payload)
        assert res_start.status_code == 200
        assert res_start.json()["takeover"] is True
        mock_redis.set.assert_called_once_with("call_takeover:456", "true", ex=86400)
        mock_redis.publish.assert_any_call("call:coaching:456", json.dumps({"takeover": True}))

        # Stop takeover
        res_stop = await client.post("/supervisor/takeover/stop", json=payload)
        assert res_stop.status_code == 200
        assert res_stop.json()["takeover"] is False
        mock_redis.delete.assert_called_once_with("call_takeover:456")
        mock_redis.publish.assert_any_call("call:coaching:456", json.dumps({"takeover": False}))


@pytest.mark.asyncio
async def test_webrtc_transport_bypass_in_takeover():
    """
    Test that when call_takeover is active, customer audio in WebRTCTransport
    bypasses the pipeline and is published directly to Redis.
    """
    mock_ws = AsyncMock()
    mock_push = AsyncMock()
    mock_collect = AsyncMock()

    transport = WebRTCTransport(
        ws=mock_ws,
        pipeline_push=mock_push,
        pipeline_collect=mock_collect,
        run_id=456
    )

    # 1. Takeover inactive: Verify audio is pushed to pipeline
    with patch("app.dependencies.rate_limit.redis_client.get", AsyncMock(return_value=None)):
        mock_ws.iter_text = MagicMock()
        # Mock generator returning one start message and one audio message
        async def mock_generator():
            yield json.dumps({"type": "start", "context": {}})
            yield json.dumps({"type": "audio", "data": "AAAA"})  # 3 bytes of raw audio
        mock_ws.iter_text.return_value = mock_generator()

        await transport._receive_loop()
        # Verify call_start and audio_in were pushed
        assert mock_push.call_count == 2
        pushed_frames = [call[0][0] for call in mock_push.call_args_list]
        assert pushed_frames[0].type == FrameType.CALL_START
        assert pushed_frames[1].type == FrameType.AUDIO_IN

    # Reset mock push
    mock_push.reset_mock()

    # 2. Takeover active: Verify audio bypasses pipeline and is published to Redis
    with patch("app.dependencies.rate_limit.redis_client.get", AsyncMock(return_value="true")), \
         patch("app.dependencies.rate_limit.redis_client.publish", new_callable=AsyncMock) as mock_publish:
        mock_ws.iter_text = MagicMock()
        async def mock_generator_takeover():
            yield json.dumps({"type": "audio", "data": "AAAA"})
        mock_ws.iter_text.return_value = mock_generator_takeover()

        await transport._receive_loop()
        
        # Verify no AUDIO_IN frames were pushed into the AI pipeline (only CALL_START fallback)
        pushed_types = [call[0][0].type for call in mock_push.call_args_list]
        assert FrameType.AUDIO_IN not in pushed_types
        
        # Verify the raw audio chunk was published to Redis instead
        mock_publish.assert_called_once_with(
            "call:audio:customer:456",
            json.dumps({"data": "AAAA"})
        )
