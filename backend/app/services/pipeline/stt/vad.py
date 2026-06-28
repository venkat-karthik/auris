import struct
import math
from loguru import logger

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import Frame, FrameType


class VADProcessor(BaseProcessor):
    """
    Energy-based Voice Activity Detector (VAD).
    Analyzes AUDIO_IN frames:
    - Emits USER_SPEAKING when user starts speaking (onset).
    - Emits USER_SILENT when user stops speaking for a set period (offset).
    - Forwards incoming frames unmodified.
    """

    def __init__(
        self,
        threshold: float = 300.0,
        silence_limit_ms: float = 1200.0,
        onset_limit_ms: float = 150.0,
    ):
        super().__init__("vad-processor")
        self.threshold = threshold
        self.silence_limit_ms = silence_limit_ms
        self.onset_limit_ms = onset_limit_ms

        self.is_speaking = False
        self.silence_duration_ms = 0.0
        self.speech_duration_ms = 0.0

    async def process_frame(self, frame: Frame) -> None:
        if frame.type == FrameType.CALL_START:
            self.is_speaking = False
            self.silence_duration_ms = 0.0
            self.speech_duration_ms = 0.0
            await self.emit(frame)

        elif frame.type == FrameType.AUDIO_IN:
            audio_data = frame.data
            if not audio_data:
                await self.emit(frame)
                return

            # 1. Calculate RMS energy in pure Python (Python 3.14 safe)
            count = len(audio_data) // 2
            if count > 0:
                try:
                    samples = struct.unpack(f"<{count}h", audio_data)
                    sum_squares = sum(s * s for s in samples)
                    rms = math.sqrt(sum_squares / count)
                except Exception as ex:
                    logger.debug(f"VAD unpack failure: {ex}")
                    rms = 0.0
            else:
                rms = 0.0

            # 2. Calculate chunk duration in milliseconds (16kHz 16-bit Mono PCM = 32000 bytes/sec)
            chunk_ms = len(audio_data) / 32.0

            # 3. Assess voice activity
            if rms >= self.threshold:
                # Speech detected
                self.speech_duration_ms += chunk_ms
                self.silence_duration_ms = 0.0

                if not self.is_speaking and self.speech_duration_ms >= self.onset_limit_ms:
                    self.is_speaking = True
                    logger.info("VAD: Voice onset detected (USER_SPEAKING)")
                    # Emit USER_SPEAKING frame to trigger TTS barge-in
                    await self.emit(Frame(type=FrameType.USER_SPEAKING))
            else:
                # Silence detected
                self.silence_duration_ms += chunk_ms
                self.speech_duration_ms = 0.0

                if self.is_speaking and self.silence_duration_ms >= self.silence_limit_ms:
                    self.is_speaking = False
                    logger.info("VAD: Voice offset detected (USER_SILENT)")
                    # Emit USER_SILENT frame to trigger STT segment translation
                    await self.emit(Frame(type=FrameType.USER_SILENT))

            # Always forward audio chunk to subsequent processors
            await self.emit(frame)
        else:
            await self.emit(frame)
