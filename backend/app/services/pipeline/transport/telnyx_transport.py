"""
Auris - Telnyx Transport
Converts μ-law 8 kHz ↔ PCM 16 kHz for Telnyx WebSocket calls.

Python 3.13 removed `audioop` from the stdlib.  We try to import
`audioop-lts` (the drop-in back-port) first, then the built-in.
"""

from __future__ import annotations

import base64
import json
from typing import AsyncGenerator, Optional

from loguru import logger

# Prefer the back-port on Python 3.13+; fall back to stdlib on older versions.
try:
    import audioop_lts as audioop  # type: ignore[import]
except ImportError:
    try:
        import audioop  # type: ignore[import]
    except ImportError:
        audioop = None  # type: ignore[assignment]


class TelnyxTransport:
    """Transport for Telnyx inbound call audio.

    Telnyx streams audio over a WebSocket in one of two formats:

    1. **JSON envelope** (media streaming):
       ``{"event": "media", "media": {"payload": "<base64-mulaw>"}}``
    2. **Raw binary** (legacy / direct): raw μ-law bytes.

    This class handles both.  Incoming μ-law 8 kHz is converted to
    16 kHz PCM 16-bit mono for the pipeline; the reverse path converts
    pipeline output back to μ-law 8 kHz before sending to Telnyx.
    """

    INPUT_RATE = 8_000
    OUTPUT_RATE = 16_000
    SAMPLE_WIDTH = 2  # bytes — 16-bit PCM

    # ------------------------------------------------------------------
    # Low-level codec helpers
    # ------------------------------------------------------------------

    @classmethod
    def ulaw_to_pcm(cls, data: bytes) -> bytes:
        """Convert μ-law bytes → 16-bit PCM."""
        if audioop is None:
            raise RuntimeError(
                "audioop is not available.  Install 'audioop-lts' for Python 3.13+: "
                "pip install audioop-lts"
            )
        return audioop.ulaw2lin(data, cls.SAMPLE_WIDTH)

    @classmethod
    def pcm_to_ulaw(cls, data: bytes) -> bytes:
        """Convert 16-bit PCM → μ-law bytes."""
        if audioop is None:
            raise RuntimeError(
                "audioop is not available.  Install 'audioop-lts' for Python 3.13+: "
                "pip install audioop-lts"
            )
        return audioop.lin2ulaw(data, cls.SAMPLE_WIDTH)

    @classmethod
    def resample(cls, data: bytes, from_rate: int, to_rate: int, state=None):
        """Resample PCM data between two rates using audioop.ratecv.

        Returns ``(resampled_bytes, new_state)``.
        """
        if audioop is None:
            raise RuntimeError("audioop is not available.  Install 'audioop-lts'.")
        return audioop.ratecv(data, cls.SAMPLE_WIDTH, 1, from_rate, to_rate, state)

    # ------------------------------------------------------------------
    # Async stream helpers
    # ------------------------------------------------------------------

    @classmethod
    async def receive_ulaw(cls, websocket) -> AsyncGenerator[bytes, None]:
        """Yield 16 kHz PCM chunks received from the Telnyx WebSocket.

        Handles both JSON-envelope (media streaming) and raw-binary frames.
        """
        state = None
        async for message in websocket.iter_text():
            raw_ulaw: Optional[bytes] = None

            # Try JSON envelope first (Telnyx media streaming format)
            if isinstance(message, str):
                try:
                    envelope = json.loads(message)
                    event = envelope.get("event", "")
                    if event == "media":
                        payload_b64 = envelope.get("media", {}).get("payload", "")
                        if payload_b64:
                            raw_ulaw = base64.b64decode(payload_b64)
                    elif event in ("connected", "start", "stop", "mark"):
                        # Control frames — ignore silently
                        continue
                    else:
                        # Unknown JSON frame — skip
                        logger.debug(f"TelnyxTransport: unknown event '{event}', skipping")
                        continue
                except (json.JSONDecodeError, Exception):
                    # Not JSON — treat as raw bytes encoded as a string
                    raw_ulaw = message.encode("latin-1")
            else:
                raw_ulaw = message  # binary frame

            if not raw_ulaw:
                continue

            try:
                pcm_8k = cls.ulaw_to_pcm(raw_ulaw)
                pcm_16k, state = cls.resample(pcm_8k, cls.INPUT_RATE, cls.OUTPUT_RATE, state)
                yield pcm_16k
            except Exception as e:
                logger.error(f"TelnyxTransport.receive_ulaw codec error: {e}")

    @classmethod
    async def send_pcm(
        cls,
        websocket,
        pcm_data: bytes,
        state=None,
    ) -> tuple[bytes, object]:
        """Convert 16 kHz PCM → μ-law 8 kHz and send to Telnyx.

        Returns ``(ulaw_bytes, new_state)`` so callers can chain resampling state.
        """
        try:
            pcm_8k, new_state = cls.resample(pcm_data, cls.OUTPUT_RATE, cls.INPUT_RATE, state)
            ulaw = cls.pcm_to_ulaw(pcm_8k)
            await websocket.send_bytes(ulaw)
            return ulaw, new_state
        except Exception as e:
            logger.error(f"TelnyxTransport.send_pcm error: {e}")
            return b"", state
