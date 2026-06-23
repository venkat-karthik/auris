"""
Auris Pipeline - Frame definitions.
Frames are the unit of data flowing through the pipeline.
Written from scratch — no pipecat dependency.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FrameType(str, Enum):
    # Audio frames
    AUDIO_IN = "audio_in"          # Raw audio bytes from caller
    AUDIO_OUT = "audio_out"        # Audio bytes to send to caller

    # Text frames
    STT_TRANSCRIPT = "stt_transcript"    # Partial or final STT result
    LLM_TEXT = "llm_text"                # Streaming LLM token
    LLM_TEXT_COMPLETE = "llm_text_complete"  # Full LLM response

    # Control frames
    CALL_START = "call_start"      # Call connected
    CALL_END = "call_end"          # Call ended
    USER_SPEAKING = "user_speaking"    # VAD: user started speaking
    USER_SILENT = "user_silent"        # VAD: user stopped speaking
    AGENT_SPEAKING = "agent_speaking"  # Agent TTS started
    AGENT_SILENT = "agent_silent"      # Agent TTS ended

    # Tool frames
    TOOL_CALL = "tool_call"        # LLM wants to call a tool
    TOOL_RESULT = "tool_result"    # Tool returned result

    # Error
    ERROR = "error"


@dataclass
class Frame:
    type: FrameType
    data: Any = None                   # type-specific payload
    metadata: dict = field(default_factory=dict)
    timestamp_ms: int = 0              # wall-clock ms since call start


# ── Typed frame constructors (convenience) ───────────────────────────────────

def audio_in(pcm: bytes, sample_rate: int = 16000) -> Frame:
    return Frame(type=FrameType.AUDIO_IN, data=pcm,
                 metadata={"sample_rate": sample_rate})


def audio_out(pcm: bytes, sample_rate: int = 16000) -> Frame:
    return Frame(type=FrameType.AUDIO_OUT, data=pcm,
                 metadata={"sample_rate": sample_rate})


def stt_transcript(text: str, is_final: bool = False, language: str = "en") -> Frame:
    return Frame(type=FrameType.STT_TRANSCRIPT,
                 data={"text": text, "is_final": is_final, "language": language})


def llm_text(token: str) -> Frame:
    return Frame(type=FrameType.LLM_TEXT, data=token)


def llm_text_complete(full_text: str, tool_calls: list | None = None) -> Frame:
    return Frame(type=FrameType.LLM_TEXT_COMPLETE,
                 data={"text": full_text, "tool_calls": tool_calls or []})


def tool_call(name: str, arguments: dict, call_id: str) -> Frame:
    return Frame(type=FrameType.TOOL_CALL,
                 data={"name": name, "arguments": arguments, "call_id": call_id})


def tool_result(call_id: str, result: Any) -> Frame:
    return Frame(type=FrameType.TOOL_RESULT,
                 data={"call_id": call_id, "result": result})


def call_start(context: dict | None = None) -> Frame:
    return Frame(type=FrameType.CALL_START, data=context or {})


def call_end(reason: str = "normal") -> Frame:
    return Frame(type=FrameType.CALL_END, data={"reason": reason})


def error_frame(message: str) -> Frame:
    return Frame(type=FrameType.ERROR, data={"message": message})
