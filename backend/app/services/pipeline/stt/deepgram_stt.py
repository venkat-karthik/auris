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
        self._is_active = True

    async def _connect_with_retry(self) -> None:
        import websockets
        import asyncio
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
        
        backoff = 0.5
        max_backoff = 8.0
        while self._is_active:
            try:
                self._ws = await websockets.connect(
                    url,
                    extra_headers={"Authorization": f"Token {self.api_key}"},
                )
                logger.info(f"Deepgram STT connected (lang={self.language}, model={self.model})")
                return
            except Exception as e:
                logger.warning(f"Deepgram STT connection failed: {e}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)

    async def process_frame(self, frame: Frame) -> None:
        if frame.type == FrameType.CALL_START:
            self._is_active = True
            await self._connect_with_retry()
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
            self._is_active = False
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
        import websockets
        import asyncio
        while self._is_active:
            try:
                if not self._ws:
                    await self._connect_with_retry()
                    if not self._ws:
                        break
                    
                async for message in self._ws:
                    if not self._is_active:
                        break
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
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Deepgram STT connection closed. Reconnecting...")
                self._ws = None
            except Exception as e:
                logger.error(f"Deepgram receive error: {e}. Reconnecting...")
                self._ws = None
                await asyncio.sleep(1.0)
