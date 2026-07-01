import asyncio
import pytest
from app.services.pipeline.frame import (
    Frame, FrameType, audio_in, audio_out, stt_transcript,
    llm_text, llm_text_complete, tool_call, tool_result,
    call_start, call_end, error_frame
)
from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.engine import PipelineEngine
from app.services.pipeline.factory import build_pipeline
from app.services.pipeline.workflow_engine import WorkflowGraphEngine, WorkflowState


class DummyMultiplierProcessor(BaseProcessor):
    def __init__(self, name: str, factor: int = 2):
        super().__init__(name)
        self.factor = factor

    async def process_frame(self, frame: Frame) -> None:
        if frame.type == FrameType.STT_TRANSCRIPT:
            text = frame.data.get("text", "")
            await self.emit(stt_transcript(text * self.factor, is_final=True))
        else:
            await self.emit(frame)


class DummyErrorProcessor(BaseProcessor):
    async def process_frame(self, frame: Frame) -> None:
        if frame.type == FrameType.STT_TRANSCRIPT:
            raise RuntimeError("Intentional processor crash")
        await self.emit(frame)


@pytest.mark.asyncio
async def test_frame_constructors():
    f_in = audio_in(b"pcm_data", 16000)
    assert f_in.type == FrameType.AUDIO_IN
    assert f_in.data == b"pcm_data"
    assert f_in.metadata["sample_rate"] == 16000

    f_out = audio_out(b"out_pcm")
    assert f_out.type == FrameType.AUDIO_OUT

    f_stt = stt_transcript("Hello world", is_final=True, language="en")
    assert f_stt.type == FrameType.STT_TRANSCRIPT
    assert f_stt.data == {"text": "Hello world", "is_final": True, "language": "en"}

    f_llm = llm_text("token")
    assert f_llm.type == FrameType.LLM_TEXT
    assert f_llm.data == "token"

    f_comp = llm_text_complete("Hello back", tool_calls=[{"id": "call_1"}])
    assert f_comp.type == FrameType.LLM_TEXT_COMPLETE
    assert f_comp.data["tool_calls"] == [{"id": "call_1"}]

    f_tool = tool_call("search", {"q": "auris"}, "c_1")
    assert f_tool.type == FrameType.TOOL_CALL

    f_res = tool_result("c_1", {"found": True})
    assert f_res.type == FrameType.TOOL_RESULT

    f_start = call_start({"room": "123"})
    assert f_start.type == FrameType.CALL_START

    f_end = call_end("hangup")
    assert f_end.type == FrameType.CALL_END

    f_err = error_frame("boom")
    assert f_err.type == FrameType.ERROR
    assert f_err.data["message"] == "boom"


@pytest.mark.asyncio
async def test_base_processor_queue_and_error():
    proc = DummyMultiplierProcessor("multiplier", factor=3)
    task = asyncio.create_task(proc.run())

    await proc.push(stt_transcript("hi"))
    res = await proc.output.get()
    assert res is not None
    assert res.type == FrameType.STT_TRANSCRIPT
    assert res.data["text"] == "hihihi"

    await proc.stop()
    res2 = await proc.output.get()
    assert res2 is None
    await task


@pytest.mark.asyncio
async def test_base_processor_error_handling():
    proc = DummyErrorProcessor("error_proc")
    task = asyncio.create_task(proc.run())

    await proc.push(stt_transcript("trigger crash"))
    err_frame = await proc.output.get()
    assert err_frame is not None
    assert err_frame.type == FrameType.ERROR
    assert "Intentional processor crash" in err_frame.data["message"]

    await proc.stop()
    await task


@pytest.mark.asyncio
async def test_pipeline_engine():
    p1 = DummyMultiplierProcessor("p1", factor=2)
    p2 = DummyMultiplierProcessor("p2", factor=3)
    engine = PipelineEngine([p1, p2])

    await engine.start()
    await engine.push(stt_transcript("a"))
    
    out = await engine.collect()
    assert out is not None
    assert out.type == FrameType.STT_TRANSCRIPT
    assert out.data["text"] == "aaaaaa"  # 'a' * 2 * 3 = 6 'a's

    await engine.stop()


def test_workflow_graph_validation():
    # Valid graph
    valid = {
        "nodes": [
            {"id": "n1", "type": "startCall"},
            {"id": "n2", "type": "agent", "data": {"system_prompt": "Hello"}},
            {"id": "n3", "type": "endCall"}
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"}
        ]
    }
    is_valid, err = WorkflowGraphEngine.validate_graph(valid)
    assert is_valid is True
    assert err is None

    # Missing start node
    no_start = {"nodes": [{"id": "n1", "type": "agent"}]}
    is_valid, err = WorkflowGraphEngine.validate_graph(no_start)
    assert is_valid is False
    assert "startCall" in err

    # Multiple start nodes
    multi_start = {
        "nodes": [
            {"id": "n1", "type": "startCall"},
            {"id": "n2", "type": "startCall"}
        ]
    }
    is_valid, err = WorkflowGraphEngine.validate_graph(multi_start)
    assert is_valid is False
    assert "multiple" in err

    # Circular loop
    loop_graph = {
        "nodes": [
            {"id": "start", "type": "startCall"},
            {"id": "loop1", "type": "agent"},
            {"id": "loop2", "type": "agent"}
        ],
        "edges": [
            {"source": "start", "target": "loop1"},
            {"source": "loop1", "target": "loop2"},
            {"source": "loop2", "target": "loop1"}
        ]
    }
    is_valid, err = WorkflowGraphEngine.validate_graph(loop_graph)
    assert is_valid is False
    assert "circular loops" in err


@pytest.mark.asyncio
async def test_workflow_state_execution():
    graph = {
        "nodes": [
            {"id": "start", "type": "startCall"},
            {"id": "qa_node", "type": "qa", "data": {"question": "What is your account id?", "expected_variable": "acct_id"}},
            {"id": "end", "type": "endCall"}
        ],
        "edges": [
            {"source": "start", "target": "qa_node"},
            {"source": "qa_node", "target": "end"}
        ]
    }

    ws = WorkflowState(graph, context_variables={"user": "Venkat"})
    prompt, should_end = await ws.execute_active_node()
    assert should_end is False
    assert "What is your account id?" in prompt
    assert ws.active_node_id == "qa_node"

    # Transition to end node
    ws.transition_to_next()
    assert ws.active_node_id == "end"
    prompt2, should_end2 = await ws.execute_active_node()
    assert should_end2 is True


def test_pipeline_factory_defaults():
    cfg = {
        "cost_tier": "standard",
        "stt": {"provider": "deepgram", "model": "nova-2"},
        "llm": {"provider": "openai", "model": "gpt-4o-mini"},
        "tts": {"provider": "elevenlabs", "voice_id": "test_voice"}
    }
    pipeline = build_pipeline(cfg, system_prompt="You are Auris.", language="en")
    assert len(pipeline.processors) == 4
    names = [p.name for p in pipeline.processors]
    assert names == ["vad-processor", "deepgram-stt", "openai-llm", "elevenlabs-tts"]
