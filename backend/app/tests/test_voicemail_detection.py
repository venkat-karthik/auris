import pytest
from unittest.mock import AsyncMock, patch
from app.services.voicemail_detection import VoicemailDetector

@pytest.mark.asyncio
@patch("openai.Audio.atranscribe", new_callable=AsyncMock)
@patch.dict("os.environ", {"OPENAI_API_KEY": "mock-key"})
async def test_detect_voicemail_whisper_positive(mock_transcribe):
    # Mock Whisper response showing voicemail cues
    mock_transcribe.return_value = {"text": "Please leave a message after the tone"}
    
    audio_bytes = b"mock audio content"
    result = await VoicemailDetector.detect(audio_bytes)
    
    assert result["is_voicemail"] is True
    assert "please leave a message" in result["transcript"].lower()


@pytest.mark.asyncio
@patch("openai.Audio.atranscribe", new_callable=AsyncMock)
@patch.dict("os.environ", {"OPENAI_API_KEY": "mock-key"})
async def test_detect_voicemail_whisper_negative(mock_transcribe):
    # Mock Whisper response showing standard customer conversation
    mock_transcribe.return_value = {"text": "Hello, I want to check my account balance"}
    
    audio_bytes = b"mock audio content"
    result = await VoicemailDetector.detect(audio_bytes)
    
    assert result["is_voicemail"] is False
    assert "hello" in result["transcript"].lower()
