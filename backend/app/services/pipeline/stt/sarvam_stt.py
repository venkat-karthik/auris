"""
Auris - Sarvam STT Processor
Real-time STT for Indian languages: Hindi, Telugu, Tamil, Kannada, etc.
Uses Sarvam AI streaming API.
Written from scratch.
"""
import asyncio
import json
from loguru import logger

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import Frame, FrameType, stt_transcript

# Sarvam language codes
SARVAM_LANGUAGE_CODES = {
    "hi": "hi-IN",   # Hindi
    "te": "te-IN",   # Telugu
    "ta": "ta-IN",   # Tamil
    "kn": "kn-IN",   # Kannada
    "mr": "mr-IN",   # Marathi
    "bn": "bn-IN",   # Bengali
    "gu": "gu-IN",   # Gujarati
    "en": "en-IN",   # English (Indian accent)
}


class SarvamSTT(BaseProcessor):
    """
    Receives AUDIO_IN frames → emits STT_TRANSCRIPT frames.
    Uses Sarvam AI streaming speech recognition for Indian languages.
    """

    def __init__(self, api_key: str, language: str = "hi"):
        super().__init__("sarvam-stt")
        self.api_key = api_key
        self.language = language
        self.language_code = SARVAM_LANGUAGE_CODES.get(language, "hi-IN")
        self._audio_buffer: list[bytes] = []
        self._processing = False

    async def process_frame(self, frame: Frame) -> None:
        if frame.type == FrameType.CALL_START:
            logger.info(f"Sarvam STT started (lang={self.language_code})")
            await self.emit(frame)

        elif frame.type == FrameType.AUDIO_IN:
            # Buffer audio chunks and transcribe on silence
            self._audio_buffer.append(frame.data)

        elif frame.type == FrameType.USER_SILENT:
            # User stopped speaking — transcribe buffered audio
            if self._audio_buffer and not self._processing:
                asyncio.create_task(self._transcribe_buffer())
            await self.emit(frame)

        elif frame.type == FrameType.CALL_END:
            if self._audio_buffer and not self._processing:
                asyncio.create_task(self._transcribe_buffer())
            await self.emit(frame)

        else:
            await self.emit(frame)

    async def _transcribe_buffer(self) -> None:
        """Send buffered audio to Sarvam REST API for transcription."""
        if not self._audio_buffer:
            return

        self._processing = True
        audio_data = b"".join(self._audio_buffer)
        self._audio_buffer = []

        try:
            import httpx
            import base64

            # Sarvam expects base64-encoded PCM audio
            audio_b64 = base64.b64encode(audio_data).decode()

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.sarvam.ai/speech-to-text",
                    headers={
                        "api-subscription-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "saarika:v2",
                        "language_code": self.language_code,
                        "audio": audio_b64,
                        "audio_format": "pcm",
                        "sample_rate": 16000,
                    },
                )

            if resp.status_code == 200:
                data = resp.json()
                text = data.get("transcript", "").strip()
                if text:
                    await self.emit(stt_transcript(
                        text=text,
                        is_final=True,
                        language=self.language,
                    ))
            else:
                logger.error(f"Sarvam STT error: {resp.status_code} {resp.text}")

        except Exception as e:
            logger.error(f"Sarvam STT transcription error: {e}")
        finally:
            self._processing = False
