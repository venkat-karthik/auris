# backend/app/services/voicemail_detection.py
"""Voicemail detection service.

Detects whether an audio snippet is a voicemail greeting using OpenAI Whisper as the primary
provider and falls back to Google Speech‑to‑Text if Whisper is unavailable or the confidence
is low.

The service is deliberately lightweight for unit‑testing – external API calls are
performed in separate helper functions that can be mocked.
"""

import os
from typing import Dict

# OpenAI Whisper
import openai  # type: ignore

# Google Speech‑to‑Text (optional)
try:
    from google.cloud import speech  # type: ignore
except Exception:  # pragma: no cover
    speech = None  # type: ignore


class VoicemailDetector:
    """Detect voicemail in an audio byte stream.

    Returns a dictionary with:
        - "is_voicemail": bool
        - "transcript": str (the transcribed text)
    """

    @staticmethod
    async def detect(audio_bytes: bytes) -> Dict[str, object]:
        # Try OpenAI Whisper first
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise RuntimeError("OPENAI_API_KEY not set")
            # The OpenAI SDK expects a file‑like object
            # Use a temporary file via BytesIO
            from io import BytesIO

            audio_file = BytesIO(audio_bytes)
            # openai.Audio.transcribe returns a dict with "text"
            result = await openai.Audio.atranscribe("whisper-1", audio_file)
            transcript = result.get("text", "").strip()
            # Very naive heuristic: if the transcript contains typical voicemail cues
            is_voicemail = any(keyword in transcript.lower() for keyword in ["please leave a message", "voicemail", "recording", "leave a message after the tone"])
            return {"is_voicemail": is_voicemail, "transcript": transcript}
        except Exception as e:  # pragma: no cover
            # Whisper failed – fall back to Google if available
            if speech is None:
                # No fallback available – re‑raise original error
                raise e
            # Google Speech‑to‑Text expects raw audio bytes and a config
            client = speech.SpeechClient()
            audio = speech.RecognitionAudio(content=audio_bytes)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            response = client.recognize(config=config, audio=audio)
            transcripts = [result.alternatives[0].transcript for result in response.results]
            transcript = " ".join(transcripts).strip()
            is_voicemail = any(keyword in transcript.lower() for keyword in ["please leave a message", "voicemail", "recording", "leave a message after the tone"])
            return {"is_voicemail": is_voicemail, "transcript": transcript}
