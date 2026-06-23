"""
Auris - ElevenLabs TTS Processor
Converts LLM text to speech audio via ElevenLabs streaming API.
Written from scratch.
"""
from loguru import logger

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import Frame, FrameType, audio_out


class ElevenLabsTTS(BaseProcessor):
    """
    Receives LLM_TEXT_COMPLETE frames → emits AUDIO_OUT frames.
    Uses ElevenLabs streaming TTS.
    """

    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel — clear, professional

    def __init__(
        self,
        api_key: str,
        voice_id: str = DEFAULT_VOICE_ID,
        model: str = "eleven_flash_v2_5",  # Low latency model
        sample_rate: int = 16000,
    ):
        super().__init__("elevenlabs-tts")
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.sample_rate = sample_rate

    async def process_frame(self, frame: Frame) -> None:
        if frame.type == FrameType.LLM_TEXT_COMPLETE:
            text = (frame.data or {}).get("text", "").strip()
            if text:
                await self._synthesize(text)
            await self.emit(frame)  # Pass through so downstream knows TTS is done

        else:
            await self.emit(frame)

    async def _synthesize(self, text: str) -> None:
        """Stream audio from ElevenLabs and emit AUDIO_OUT frames."""
        try:
            import httpx

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            }
            payload = {
                "text": text,
                "model_id": self.model,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                "output_format": f"pcm_{self.sample_rate}",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        logger.error(f"ElevenLabs TTS error: {resp.status_code}")
                        return
                    async for chunk in resp.aiter_bytes(chunk_size=4096):
                        if chunk:
                            await self.emit(audio_out(chunk, self.sample_rate))

        except Exception as e:
            logger.error(f"ElevenLabs TTS synthesis error: {e}")
