import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from app.main import app
from app.models.agent import Agent
from app.models.organization import Organization
from app.services.pipeline.frame import Frame, FrameType

class MockPipelineEngine:
    def __init__(self, *args, **kwargs):
        self.collect_count = 0
        self.processors = []

    async def start(self):
        pass

    async def push(self, frame):
        pass

    async def collect(self):
        self.collect_count += 1
        if self.collect_count > 2:
            # Exit loop after two frames
            return None
        return Frame(type=FrameType.AUDIO_OUT, data=b"mock_pcm_data_16k")

    async def stop(self):
        pass

@pytest.mark.asyncio
async def test_inbound_telnyx(client: AsyncClient):
    response = await client.post("/telephony/inbound/telnyx?call_control_id=cc123&org_id=1&agent_id=2")
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    assert "cc123" in response.text
    assert "org_id=1" in response.text
    assert "agent_id=2" in response.text

@pytest.mark.asyncio
async def test_telephony_ws_flow(db_session: AsyncSession, test_org, test_user):
    # Setup dummy agent in DB
    agent = Agent(
        org_id=test_org.id,
        created_by=test_user.id,
        name="Telephony Agent",
        description="Helper prompt",
        model_config={"stt": {"provider": "deepgram"}}
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    # We need to mock:
    # 1. build_pipeline to return our MockPipelineEngine
    # 2. TelnyxTransport.receive_ulaw to yield fake ulaw audio bytes
    # 3. TelnyxTransport.send_pcm to capture sent bytes
    
    async def mock_receive_ulaw(websocket):
        yield b"chunk1"
        yield b"chunk2"

    mock_send_pcm = AsyncMock()

    with (
        patch("app.routes.telephony.build_pipeline", return_value=MockPipelineEngine()),
        patch("app.routes.telephony.TelnyxTransport.receive_ulaw", side_effect=mock_receive_ulaw),
        patch("app.routes.telephony.TelnyxTransport.send_pcm", mock_send_pcm)
    ):
        # We can use Starlette's TestClient to test the WebSocket endpoint sync-style
        client = TestClient(app)
        with client.websocket_connect(
            f"/api/v1/telephony/ws/telnyx?call_control_id=cc123&org_id={test_org.id}&agent_id={agent.id}"
        ) as ws:
            # The websocket connection will accept, query DB, start pipeline,
            # process the mocked generator yields, send PCM, and gracefully stop.
            import time
            time.sleep(0.5)

    # Verify send_pcm was called with output data
    assert mock_send_pcm.call_count > 0
    sent_data = mock_send_pcm.call_args[0][1]
    assert sent_data == b"mock_pcm_data_16k"
