"""
Auris - Sarvam TTS Processor
Indian language TTS: Hindi, Telugu, Tamil, etc.
Uses Sarvam AI Bulbul v3 model — best quality for Indian languages.
Written from scratch.
"""
from loguru import logger

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import Frame, FrameType, audio_out

SARVAM_VOICES = {
    "hi": "meera",    # Hindi female
    "te": "pavithra", # Telugu female
    "ta": "maya",     # Tamil female
    "en": "arjun",    # English (Indian accent)
    "kn": "amol",     # Kannada
    "mr": "amol",     # Marathi
}


class SarvamTTS(BaseProcessor):
    """
    Receives LLM_TEXT_COMPLETE frames → emits AUDIO_OUT frames.
    Uses Sarvam AI for Indian language synthesis.
    """

    def __init__(
        self,
        api_key: str,
        language: str = "hi",
        sample_rate: int = 16000,
    ):
        super().__init__("sarvam-tts")
        self.api_key = api_key
        self.language = language
        self.speaker = SARVAM_VOICES.get(language, "meera")
        self.sample_rate = sample_rate

    async def process_frame(self, frame: Frame) -> None:
        if frame.type == FrameType.LLM_TEXT_COMPLETE:
            text = (frame.data or {}).get("text", "").strip()
            if text:
                await self._synthesize(text)
            await self.emit(frame)
        else:
            await self.emit(frame)

    async def _synthesize(self, text: str) -> None:
        try:
            import base64
            import httpx

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.sarvam.ai/text-to-speech",
                    headers={
                        "api-subscription-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "inputs": [text],
                        "target_language_code": f"{self.language}-IN",
                        "speaker": self.speaker,
                        "model": "bulbul:v3",
                        "speech_sample_rate": self.sample_rate,
                        "enable_preprocessing": True,
                    },
                )

            if resp.status_code != 200:
                logger.error(f"Sarvam TTS error: {resp.status_code} {resp.text}")
                return

            data = resp.json()
            audio_b64 = data.get("audios", [None])[0]
            if audio_b64:
                pcm = base64.b64decode(audio_b64)
                # Emit in chunks for smooth streaming
                chunk_size = 4096
                for i in range(0, len(pcm), chunk_size):
                    await self.emit(audio_out(pcm[i:i+chunk_size], self.sample_rate))

        except Exception as e:
            logger.error(f"Sarvam TTS error: {e}")
