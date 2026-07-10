import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

from app.services.pipeline.frame import Frame, FrameType
from app.services.pipeline.llm.openai_llm import OpenAILLM
from app.services.pipeline.llm.anthropic_llm import AnthropicLLM


@pytest.mark.asyncio
async def test_link_click_tracking_redirect(client: AsyncClient):
    """
    Test that clicking the short link redirects to the original destination URL,
    and publishes the click event to Redis Pub/Sub.
    """
    mock_val = json.dumps({
        "call_run_id": 123,
        "original_url": "https://example.com/invoice/999",
        "clicked": False
    })

    with patch("app.routes.links.redis_client") as mock_redis:
        mock_redis.get = AsyncMock(return_value=mock_val)
        mock_redis.publish = AsyncMock()
        mock_redis.set = AsyncMock()

        # The base_url of client is configured as http://testserver/api/v1,
        # so "/links/click/test_token" resolves correctly.
        response = await client.get("/links/click/test_token")

        # Verify 302/307 Redirect
        assert response.status_code in (302, 307)
        assert response.headers["location"] == "https://example.com/invoice/999"

        # Verify event was published to the correct Pub/Sub channel
        mock_redis.publish.assert_called_once_with(
            "call:link_clicks:123",
            json.dumps({"event": "link_clicked", "url": "https://example.com/invoice/999"})
        )

        # Verify the clicked state was stored back in Redis
        called_args = mock_redis.set.call_args[0]
        assert called_args[0] == "tracked_link:test_token"
        saved_data = json.loads(called_args[1])
        assert saved_data["clicked"] is True


@pytest.mark.asyncio
async def test_openai_llm_system_transcript_handling():
    """
    Test that STT transcripts beginning with '[SYSTEM' are handled
    as system messages rather than user messages in OpenAILLM.
    """
    processor = OpenAILLM(api_key="mock-key")

    # Initialize call
    await processor.process_frame(Frame(type=FrameType.CALL_START, data={}))

    # Send system notice frame
    await processor.process_frame(Frame(
        type=FrameType.STT_TRANSCRIPT,
        data={"text": "[SYSTEM NOTICE: User clicked link https://example.com]", "is_final": True}
    ))

    # Verify that the system prompt message and our system notice message are both present
    assert len(processor._messages) == 2
    assert processor._messages[0]["role"] == "system"
    assert processor._messages[1]["role"] == "system"
    assert "User clicked link" in processor._messages[1]["content"]


@pytest.mark.asyncio
async def test_anthropic_llm_system_transcript_handling():
    """
    Test that STT transcripts beginning with '[SYSTEM' are handled
    as system messages and merged into the system prompt parameter in AnthropicLLM.
    """
    processor = AnthropicLLM(
        api_key="actual-anthropic-key",  # Must not start with "mock" to trigger generate stream call
        system_prompt="Initial prompt."
    )

    # Initialize call
    await processor.process_frame(Frame(type=FrameType.CALL_START, data={}))

    # Send system notice frame
    await processor.process_frame(Frame(
        type=FrameType.STT_TRANSCRIPT,
        data={"text": "[SYSTEM NOTICE: Link clicked]", "is_final": True}
    ))

    # Verify it is appended as system message
    assert len(processor._messages) == 1
    assert processor._messages[0]["role"] == "system"

    # Mock anthropic async stream call to verify the prompt merging
    with patch("anthropic.AsyncAnthropic") as mock_client:
        mock_instance = MagicMock()
        mock_stream = AsyncMock()
        # Ensure we return a mock stream
        mock_stream.__aenter__.return_value = AsyncMock()
        mock_instance.messages.stream = mock_stream
        mock_client.return_value = mock_instance

        # Trigger generation
        await processor._generate()

        # Assert that the system prompt passed to Claude contains the merged notice
        args, kwargs = mock_stream.call_args
        assert "system" in kwargs
        assert "Initial prompt." in kwargs["system"]
        assert "[SYSTEM NOTICE: Link clicked]" in kwargs["system"]
