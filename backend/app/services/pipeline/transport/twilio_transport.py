"""
Auris - Twilio Transport
Converts μ-law 8 kHz ↔ PCM 16 kHz for Twilio Media Stream WebSockets.
"""

from __future__ import annotations

import base64
import json
from typing import AsyncGenerator, Optional, Tuple

from loguru import logger

try:
    import audioop_lts as audioop  # type: ignore[import]
except ImportError:
    try:
        import audioop  # type: ignore[import]
    except ImportError:
        audioop = None  # type: ignore[assignment]


class TwilioTransport:
    """Transport for Twilio inbound Media Stream calls.

    Twilio sends and receives audio frames encoded as base64 μ-law.
    Formats:
    - Receive: {"event": "media", "media": {"payload": "..."}}
    - Send: {"event": "media", "streamSid": "...", "media": {"payload": "..."}}
    """

    INPUT_RATE = 8_000
    OUTPUT_RATE = 16_000
    SAMPLE_WIDTH = 2

    @classmethod
    def ulaw_to_pcm(cls, data: bytes) -> bytes:
        if audioop is None:
            raise RuntimeError("audioop is not available. Install 'audioop-lts'.")
        return audioop.ulaw2lin(data, cls.SAMPLE_WIDTH)

    @classmethod
    def pcm_to_ulaw(cls, data: bytes) -> bytes:
        if audioop is None:
            raise RuntimeError("audioop is not available. Install 'audioop-lts'.")
        return audioop.lin2ulaw(data, cls.SAMPLE_WIDTH)

    @classmethod
    def resample(cls, data: bytes, from_rate: int, to_rate: int, state=None):
        if audioop is None:
            raise RuntimeError("audioop is not available. Install 'audioop-lts'.")
        return audioop.ratecv(data, cls.SAMPLE_WIDTH, 1, from_rate, to_rate, state)

    @classmethod
    async def send_pcm(
        cls,
        websocket,
        stream_sid: str,
        pcm_data: bytes,
        state=None,
    ) -> Tuple[bytes, object]:
        """Convert 16 kHz PCM → μ-law 8 kHz base64 and send envelope to Twilio."""
        try:
            pcm_8k, new_state = cls.resample(pcm_data, cls.OUTPUT_RATE, cls.INPUT_RATE, state)
            ulaw = cls.pcm_to_ulaw(pcm_8k)
            payload = base64.b64encode(ulaw).decode("utf-8")
            
            envelope = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": payload
                }
            }
            await websocket.send_text(json.dumps(envelope))
            return ulaw, new_state
        except Exception as e:
            logger.error(f"TwilioTransport.send_pcm error: {e}")
            return b"", state
