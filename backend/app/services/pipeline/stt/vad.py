import struct
import math
from loguru import logger

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import Frame, FrameType


class VADProcessor(BaseProcessor):
    """
    Voice Activity Detector (VAD).
    Uses WebRTC VAD (webrtcvad) if available for ML-based accuracy.
    Falls back to Energy-based RMS detection if webrtcvad is not installed.
    
    Analyzes AUDIO_IN frames:
    - Emits USER_SPEAKING when user starts speaking (onset).
    - Emits USER_SILENT when user stops speaking for a set period (offset).
    - Forwards incoming frames unmodified to maintain sub-millisecond audio transit latency.
    """

    def __init__(
        self,
        threshold: float = 300.0,
        silence_limit_ms: float = 1200.0,
        onset_limit_ms: float = 150.0,
        mode: int = 3,
    ):
        super().__init__("vad-processor")
        self.threshold = threshold
        self.silence_limit_ms = silence_limit_ms
        self.onset_limit_ms = onset_limit_ms
        self.mode = mode

        self.is_speaking = False
        self.silence_duration_ms = 0.0
        self.speech_duration_ms = 0.0
        self.buffer = b""

        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(mode)
            logger.info(f"VADProcessor: Initialized WebRTC VAD (aggressiveness={mode})")
        except ImportError:
            self.vad = None
            logger.warning("VADProcessor: webrtcvad not installed. Falling back to energy-based RMS detection.")

    def _calculate_rms(self, audio_data: bytes) -> float:
        count = len(audio_data) // 2
        if count > 0:
            try:
                samples = struct.unpack(f"<{count}h", audio_data)
                sum_squares = sum(s * s for s in samples)
                return math.sqrt(sum_squares / count)
            except Exception as ex:
                logger.debug(f"VAD unpack failure: {ex}")
                return 0.0
        return 0.0

    async def process_frame(self, frame: Frame) -> None:
        if frame.type == FrameType.CALL_START:
            self.is_speaking = False
            self.silence_duration_ms = 0.0
            self.speech_duration_ms = 0.0
            self.buffer = b""
            await self.emit(frame)

        elif frame.type == FrameType.AUDIO_IN:
            audio_data = frame.data
            if not audio_data:
                await self.emit(frame)
                return

            is_active = False
            chunk_ms = 0.0

            if self.vad:
                self.buffer += audio_data
                # 30ms at 16kHz, 16-bit mono PCM = 960 bytes
                frame_bytes = 960
                frame_duration_ms = 30.0

                speech_detected = False
                processed_any = False

                while len(self.buffer) >= frame_bytes:
                    chunk = self.buffer[:frame_bytes]
                    self.buffer = self.buffer[frame_bytes:]
                    processed_any = True
                    try:
                        if self.vad.is_speech(chunk, 16000):
                            speech_detected = True
                    except Exception as e:
                        logger.debug(f"WebRTC VAD execution failed, falling back to RMS: {e}")
                        speech_detected = self._calculate_rms(chunk) >= self.threshold

                if not processed_any:
                    # Keep accumulating bytes and forward audio chunk
                    await self.emit(frame)
                    return

                chunk_ms = frame_duration_ms
                is_active = speech_detected
            else:
                # Fallback to energy-based RMS VAD
                rms = self._calculate_rms(audio_data)
                chunk_ms = len(audio_data) / 32.0  # 16kHz 16-bit mono = 32 bytes/ms
                is_active = rms >= self.threshold

            # Assess speech transitions
            if is_active:
                self.speech_duration_ms += chunk_ms
                self.silence_duration_ms = 0.0

                if not self.is_speaking and self.speech_duration_ms >= self.onset_limit_ms:
                    self.is_speaking = True
                    logger.info("VAD: Voice onset detected (USER_SPEAKING)")
                    await self.emit(Frame(type=FrameType.USER_SPEAKING))
            else:
                self.silence_duration_ms += chunk_ms
                self.speech_duration_ms = 0.0

                if self.is_speaking and self.silence_duration_ms >= self.silence_limit_ms:
                    self.is_speaking = False
                    logger.info("VAD: Voice offset detected (USER_SILENT)")
                    await self.emit(Frame(type=FrameType.USER_SILENT))

            # Forward the audio frame downstream
            await self.emit(frame)
        else:
            await self.emit(frame)
