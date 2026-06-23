import audioop
from typing import AsyncGenerator

class TelnyxTransport:
    """Transport for Telnyx inbound call audio.

    Telnyx sends μ‑law 8kHz audio frames over a WebSocket. This class converts
    the incoming μ‑law bytes to 16kHz PCM (the format expected by the pipeline)
    and provides a simple async generator that yields PCM chunks. The reverse
    conversion is also provided for sending audio back to Telnyx.
    """

    INPUT_RATE = 8000
    OUTPUT_RATE = 16000
    SAMPLE_WIDTH = 2  # 16‑bit PCM

    @staticmethod
    def ulaw_to_pcm(data: bytes) -> bytes:
        """Convert μ‑law bytes to 16‑bit PCM.
        """
        return audioop.ulaw2lin(data, TelnyxTransport.SAMPLE_WIDTH)

    @staticmethod
    def pcm_to_ulaw(data: bytes) -> bytes:
        """Convert 16‑bit PCM to μ‑law.
        """
        return audioop.lin2ulaw(data, TelnyxTransport.SAMPLE_WIDTH)

    @staticmethod
    def resample_pcm(data: bytes) -> bytes:
        """Resample 8kHz PCM to 16kHz using simple duplication.
        For a production system you would use a proper resampler; here we
        duplicate each sample to double the sample rate.
        """
        # Convert to 8kHz linear PCM first (already 16‑bit after ulaw conversion)
        # Duplicate each 2‑byte sample
        doubled = b"".join([data[i:i+2] * 2 for i in range(0, len(data), 2)])
        return doubled

    @classmethod
    async def receive_ulaw(cls, websocket) -> AsyncGenerator[bytes, None]:
        """Yield PCM data received from the Telnyx WebSocket.
        The caller iterates over the generator to feed audio into the pipeline.
        """
        async for message in websocket.iter_text():
            # Telnyx sends raw binary in text base64? For simplicity assume binary.
            raw_ulaw = message.encode() if isinstance(message, str) else message
            pcm = cls.ulaw_to_pcm(raw_ulaw)
            # Resample to 16kHz
            pcm_16k = cls.resample_pcm(pcm)
            yield pcm_16k

    @classmethod
    async def send_pcm(cls, websocket, pcm_data: bytes) -> None:
        """Send PCM data back to Telnyx as μ‑law.
        """
        # Down‑sample from 16kHz to 8kHz by halving sample pairs
        pcm_8k = b"".join([pcm_data[i:i+2] for i in range(0, len(pcm_data), 4)])
        ulaw = cls.pcm_to_ulaw(pcm_8k)
        await websocket.send_bytes(ulaw)
