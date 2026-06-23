"""
Auris - Deepgram STT Processor
Real-time streaming STT via Deepgram WebSocket API.
Supports: English, and any language Deepgram supports.
Written from scratch.
"""
import json
from loguru import logger

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import Frame, FrameType, stt_transcript


class DeepgramSTT(BaseProcessor):
    """
    Receives AUDIO_IN frames → emits STT_TRANSCRIPT frames.
    Uses Deepgram streaming WebSocket API.
    """

    def __init__(self, api_key: str, language: str = "en", model: str = "nova-2"):
        super().__init__("deepgram-stt")
        self.api_key = api_key
        self.language = language
        self.model = model
        self._ws = None

    async def _connect(self) -> None:
        import websockets
        params = (
            f"model={self.model}"
            f"&language={self.language}"
            f"&encoding=linear16"
            f"&sample_rate=16000"
            f"&channels=1"
            f"&interim_results=true"
            f"&endpointing=300"
            f"&utterance_end_ms=1000"
        )
        url = f"wss://api.deepgram.com/v1/listen?{params}"
        self._ws = await websockets.connect(
            url,
            extra_headers={"Authorization": f"Token {self.api_key}"},
        )
        logger.info(f"Deepgram STT connected (lang={self.language}, model={self.model})")

    async def process_frame(self, frame: Frame) -> None:
        if frame.type == FrameType.CALL_START:
            await self._connect()
            # Start listener task
            import asyncio
            asyncio.create_task(self._receive_transcripts())
            await self.emit(frame)

        elif frame.type == FrameType.AUDIO_IN:
            if self._ws:
                try:
                    await self._ws.send(frame.data)
                except Exception as e:
                    logger.error(f"Deepgram send error: {e}")

        elif frame.type == FrameType.CALL_END:
            if self._ws:
                try:
                    await self._ws.send(json.dumps({"type": "CloseStream"}))
                    await self._ws.close()
                except Exception:
                    pass
            await self.emit(frame)

        else:
            # Pass through all other frames
            await self.emit(frame)

    async def _receive_transcripts(self) -> None:
        """Background task: reads Deepgram responses and emits transcript frames."""
        try:
            async for message in self._ws:
                data = json.loads(message)
                channel = data.get("channel", {})
                alternatives = channel.get("alternatives", [])
                if not alternatives:
                    continue

                text = alternatives[0].get("transcript", "").strip()
                if not text:
                    continue

                is_final = data.get("is_final", False)
                speech_final = data.get("speech_final", False)

                await self.emit(stt_transcript(
                    text=text,
                    is_final=is_final or speech_final,
                    language=self.language,
                ))
        except Exception as e:
            logger.error(f"Deepgram receive error: {e}")
