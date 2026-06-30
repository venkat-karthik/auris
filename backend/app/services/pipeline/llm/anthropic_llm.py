"""
Auris - Anthropic LLM Processor
Streaming chat completions supporting Anthropic tools.
Written from scratch.
"""
import json
from loguru import logger

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import (
    Frame, FrameType, llm_text, llm_text_complete, tool_call,
)


class AnthropicLLM(BaseProcessor):
    """
    Receives STT_TRANSCRIPT (final) + TOOL_RESULT frames.
    Emits LLM_TEXT (streaming tokens) + LLM_TEXT_COMPLETE + TOOL_CALL frames.
    Uses Anthropic's messages streaming API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        system_prompt: str = "You are a helpful voice assistant.",
        temperature: float = 0.7,
        max_tokens: int = 500,
        initial_message: str | None = None,
    ):
        super().__init__("anthropic-llm")
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.initial_message = initial_message
        self._messages: list[dict] = []
        self._tools: list[dict] = []
        self._gen_task = None

    def set_tools(self, tools: list[dict]) -> None:
        """Set available tools for function calling."""
        self._tools = tools

    async def process_frame(self, frame: Frame) -> None:
        import asyncio

        if frame.type == FrameType.CALL_START:
            # Initialize conversation
            self._messages = []
            
            # Incorporate system prompt and initial context
            context = frame.data or {}
            
            # Handle initial message config
            initial_msg = self.initial_message
            if not initial_msg and context.get("call_type") == "outbound":
                initial_msg = "Hello"
                
            if initial_msg:
                self._messages.append({"role": "user", "content": initial_msg})
                self._gen_task = asyncio.create_task(self._generate())

            await self.emit(frame)

        elif frame.type == FrameType.STT_TRANSCRIPT:
            data = frame.data or {}
            if not data.get("is_final"):
                return
            text = data.get("text", "").strip()
            if not text:
                return
            self._messages.append({"role": "user", "content": text})
            
            if self._gen_task and not self._gen_task.done():
                self._gen_task.cancel()
            self._gen_task = asyncio.create_task(self._generate())

        elif frame.type == FrameType.TOOL_RESULT:
            data = frame.data or {}
            self._messages.append({
                "role": "tool",
                "tool_call_id": data["call_id"],
                "content": json.dumps(data["result"]),
            })
            if self._gen_task and not self._gen_task.done():
                self._gen_task.cancel()
            self._gen_task = asyncio.create_task(self._generate())

        elif frame.type == FrameType.USER_SPEAKING:
            if self._gen_task and not self._gen_task.done():
                self._gen_task.cancel()
                logger.info("AnthropicLLM: Canceled current active generation due to USER_SPEAKING")
            await self.emit(frame)

        elif frame.type == FrameType.CALL_END:
            if self._gen_task and not self._gen_task.done():
                self._gen_task.cancel()
            await self.emit(frame)

        else:
            await self.emit(frame)

    async def _generate(self) -> None:
        """Call Anthropic and stream the response."""
        try:
            import anthropic
        except ImportError:
            logger.error("anthropic SDK is not installed. Falling back.")
            await self.emit(llm_text_complete("Anthropic processor is missing dependencies."))
            return

        if not self.api_key or self.api_key.startswith("mock"):
            # Mock mode fallback
            logger.warning("Using mock response for AnthropicLLM (no API key)")
            await self.emit(llm_text("Hello, I am Claude."))
            complete_frame = llm_text_complete("Hello, I am Claude.")
            complete_frame.metadata["usage"] = {
                "input_tokens": 5,
                "output_tokens": 5
            }
            await self.emit(complete_frame)
            return

        import os
        has_langfuse = bool(os.getenv("LANGFUSE_PUBLIC_KEY"))
        trace = None
        generation = None
        if has_langfuse:
            try:
                from langfuse import Langfuse
                lf = Langfuse()
                trace = lf.trace(name="voice-call-turn", metadata={"model": self.model})
                generation = trace.generation(
                    name="anthropic-llm-generate",
                    model=self.model,
                    input=self._messages,
                )
            except Exception as ex:
                logger.error(f"Langfuse trace init failed: {ex}")

        # Convert OpenAI tools format to Anthropic format
        anthropic_tools = []
        for t in self._tools:
            if t.get("type") == "function":
                fn = t["function"]
                anthropic_tools.append({
                    "name": fn["name"],
                    "description": fn["description"],
                    "input_schema": fn["parameters"]
                })

        # Translate conversation history to Anthropic format
        anthropic_messages = []
        for msg in self._messages:
            if msg["role"] == "system":
                continue
            elif msg["role"] == "user":
                anthropic_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                if "tool_calls" in msg:
                    content = []
                    if msg.get("content"):
                        content.append({"type": "text", "text": msg["content"]})
                    for tc in msg["tool_calls"]:
                        args = tc["function"]["arguments"]
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                args = {}
                        content.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "input": args
                        })
                    anthropic_messages.append({"role": "assistant", "content": content})
                else:
                    anthropic_messages.append({"role": "assistant", "content": msg["content"]})
            elif msg["role"] == "tool":
                tool_result_content = {
                    "type": "tool_result",
                    "tool_use_id": msg["tool_call_id"],
                    "content": msg["content"]
                }
                if anthropic_messages and anthropic_messages[-1]["role"] == "user" and isinstance(anthropic_messages[-1]["content"], list):
                    anthropic_messages[-1]["content"].append(tool_result_content)
                else:
                    anthropic_messages.append({"role": "user", "content": [tool_result_content]})

        # If history is empty (e.g. no user start), Anthropic requires messages. So we ensure a user message exists
        if not anthropic_messages:
            anthropic_messages.append({"role": "user", "content": "Hello"})

        full_text = ""
        tool_calls_raw = {}
        prompt_tokens = 0
        completion_tokens = 0

        try:
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            async with client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=anthropic_messages,
                tools=anthropic_tools if anthropic_tools else None
            ) as stream:
                async for event in stream:
                    if event.type == "message_start":
                        prompt_tokens = event.message.usage.input_tokens
                    elif event.type == "message_delta":
                        if hasattr(event, "usage") and event.usage:
                            completion_tokens = event.usage.output_tokens
                    elif event.type == "content_block_start":
                        cb = event.content_block
                        if cb.type == "tool_use":
                            tool_calls_raw[event.index] = {
                                "id": cb.id,
                                "name": cb.name,
                                "arguments": ""
                            }
                    elif event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            full_text += delta.text
                            await self.emit(llm_text(delta.text))
                        elif delta.type == "input_json_delta":
                            idx = event.index
                            if idx in tool_calls_raw:
                                tool_calls_raw[idx]["arguments"] += delta.partial_json

        except Exception as e:
            logger.error(f"Anthropic LLM stream error: {e}")
            if generation:
                generation.end(status_message=str(e), level="ERROR")
            await self.emit(llm_text_complete("I'm sorry, I had a problem. Please try again."))
            return

        if generation:
            try:
                generation.end(
                    output=full_text or str(tool_calls_raw),
                    usage={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens
                    }
                )
            except Exception as ex:
                logger.error(f"Langfuse generation end failed: {ex}")

        # Emit tool calls
        tool_call_frames = []
        for tc in tool_calls_raw.values():
            try:
                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
            except json.JSONDecodeError:
                args = {}
            frame = tool_call(name=tc["name"], arguments=args, call_id=tc["id"])
            tool_call_frames.append({"name": tc["name"], "call_id": tc["id"]})
            await self.emit(frame)

        # Update message history
        if full_text:
            self._messages.append({"role": "assistant", "content": full_text})
        elif tool_calls_raw:
            self._messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    }
                    for tc in tool_calls_raw.values()
                ],
            })

        complete_frame = llm_text_complete(full_text, tool_calls=tool_call_frames)
        complete_frame.metadata["usage"] = {
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens
        }
        await self.emit(complete_frame)
