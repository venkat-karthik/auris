import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.voicemail_detection import VoicemailDetector

@pytest.mark.asyncio
@patch("openai.AsyncOpenAI")
@patch.dict("os.environ", {"OPENAI_API_KEY": "mock-key"})
async def test_detect_voicemail_whisper_positive(mock_async_openai):
    mock_client = MagicMock()
    mock_transcription = MagicMock()
    mock_transcription.text = "Please leave a message after the tone"
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)
    mock_async_openai.return_value = mock_client
    
    audio_bytes = b"mock audio content"
    result = await VoicemailDetector.detect(audio_bytes)
    
    assert result["is_voicemail"] is True
    assert "please leave a message" in result["transcript"].lower()


@pytest.mark.asyncio
@patch("openai.AsyncOpenAI")
@patch.dict("os.environ", {"OPENAI_API_KEY": "mock-key"})
async def test_detect_voicemail_whisper_negative(mock_async_openai):
    mock_client = MagicMock()
    mock_transcription = MagicMock()
    mock_transcription.text = "Hello, I want to check my account balance"
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)
    mock_async_openai.return_value = mock_client
    
    audio_bytes = b"mock audio content"
    result = await VoicemailDetector.detect(audio_bytes)
    
    assert result["is_voicemail"] is False
    assert "hello" in result["transcript"].lower()
