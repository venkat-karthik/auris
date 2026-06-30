"""
Auris - Cartesia TTS Processor
Converts LLM text to speech audio via Cartesia streaming API.
Written from scratch.
"""
from loguru import logger

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import Frame, FrameType, audio_out


class CartesiaTTS(BaseProcessor):
    """
    Receives LLM_TEXT_COMPLETE frames → emits AUDIO_OUT frames.
    Uses Cartesia's raw audio bytes endpoint.
    """

    DEFAULT_VOICE_ID = "a0e9987c-38cf-4a14-b80c-2d04ca035b44"  # Sonic general English voice

    def __init__(
        self,
        api_key: str,
        voice_id: str = DEFAULT_VOICE_ID,
        model: str = "sonic-2",
        sample_rate: int = 16000,
    ):
        super().__init__("cartesia-tts")
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.sample_rate = sample_rate
        self._tts_task = None

    async def process_frame(self, frame: Frame) -> None:
        import asyncio

        if frame.type == FrameType.LLM_TEXT_COMPLETE:
            text = (frame.data or {}).get("text", "").strip()
            if text:
                if self._tts_task and not self._tts_task.done():
                    self._tts_task.cancel()
                self._tts_task = asyncio.create_task(self._synthesize(text))
            await self.emit(frame)

        elif frame.type == FrameType.USER_SPEAKING:
            if self._tts_task and not self._tts_task.done():
                self._tts_task.cancel()
                logger.info("CartesiaTTS: Canceled current active TTS stream due to USER_SPEAKING")
            await self.emit(frame)

        else:
            await self.emit(frame)

    async def _synthesize(self, text: str) -> None:
        """Stream audio from Cartesia and emit AUDIO_OUT frames."""
        try:
            import httpx

            url = "https://api.cartesia.ai/tts/bytes"
            headers = {
                "X-API-Key": self.api_key,
                "Cartesia-Version": "2024-06-10",
                "Content-Type": "application/json",
            }
            
            payload = {
                "transcript": text,
                "model_id": self.model,
                "voice": {
                    "mode": "id",
                    "id": self.voice_id,
                },
                "output_format": {
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": self.sample_rate,
                },
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        err_text = await resp.aread()
                        logger.error(f"Cartesia TTS error: {resp.status_code} - {err_text.decode('utf-8', errors='ignore')}")
                        return
                    async for chunk in resp.aiter_bytes(chunk_size=4096):
                        if chunk:
                            await self.emit(audio_out(chunk, self.sample_rate))

        except Exception as e:
            logger.error(f"Cartesia TTS synthesis error: {e}")
