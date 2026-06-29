# backend/app/services/voicemail_detection.py
"""Voicemail detection service.

Detects whether an audio snippet is a voicemail greeting using OpenAI Whisper
(via the current openai >= 1.0 SDK) as the primary provider and falls back to
Google Speech-to-Text if available.
"""

import io
import os
from typing import Dict

# Google Speech-to-Text (optional)
try:
    from google.cloud import speech  # type: ignore
except Exception:  # pragma: no cover
    speech = None  # type: ignore

VOICEMAIL_KEYWORDS = [
    "please leave a message",
    "voicemail",
    "recording",
    "leave a message after the tone",
    "not available",
    "after the beep",
]


def add_wav_header(pcm_bytes: bytes, sample_rate: int = 16000, num_channels: int = 1, bits_per_sample: int = 16) -> bytes:
    import struct
    byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
    block_align = num_channels * (bits_per_sample // 8)
    
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + len(pcm_bytes),
        b'WAVE',
        b'fmt ',
        16,
        1,  # PCM
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        len(pcm_bytes)
    )
    return header + pcm_bytes


class VoicemailDetector:
    """Detect voicemail in a raw PCM byte stream.

    Returns a dictionary with:
        - "is_voicemail": bool
        - "transcript": str
    """

    @staticmethod
    async def detect(audio_bytes: bytes) -> Dict[str, object]:
        openai_api_key = os.getenv("OPENAI_API_KEY")

        # ── OpenAI Whisper (SDK >= 1.0) ───────────────────────────────────────
        if openai_api_key:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=openai_api_key)

                # The SDK requires a file-like object with a `.name` attribute
                # so it can infer the audio format (we send raw PCM as .wav).
                wav_bytes = add_wav_header(audio_bytes)
                audio_file = io.BytesIO(wav_bytes)
                audio_file.name = "audio.wav"

                transcription = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                )
                transcript = transcription.text.strip() if transcription.text else ""
                is_voicemail = any(kw in transcript.lower() for kw in VOICEMAIL_KEYWORDS)
                return {"is_voicemail": is_voicemail, "transcript": transcript}
            except Exception as e:  # pragma: no cover
                # Fall through to Google fallback
                pass

        # ── Google Speech-to-Text fallback ────────────────────────────────────
        if speech is not None:
            try:
                g_client = speech.SpeechClient()
                audio = speech.RecognitionAudio(content=audio_bytes)
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                )
                response = g_client.recognize(config=config, audio=audio)
                transcripts = [
                    result.alternatives[0].transcript
                    for result in response.results
                    if result.alternatives
                ]
                transcript = " ".join(transcripts).strip()
                is_voicemail = any(kw in transcript.lower() for kw in VOICEMAIL_KEYWORDS)
                return {"is_voicemail": is_voicemail, "transcript": transcript}
            except Exception:
                pass

        # ── No provider available ─────────────────────────────────────────────
        return {"is_voicemail": False, "transcript": ""}
