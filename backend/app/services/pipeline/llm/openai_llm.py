"""
Auris - OpenAI LLM Processor
Streaming chat completions. Handles tool calls.
Written from scratch.
"""
import json
from loguru import logger
from openai import AsyncOpenAI

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import (
    Frame, FrameType, llm_text, llm_text_complete, tool_call,
)


class OpenAILLM(BaseProcessor):
    """
    Receives STT_TRANSCRIPT (final) + TOOL_RESULT frames.
    Emits LLM_TEXT (streaming tokens) + LLM_TEXT_COMPLETE + TOOL_CALL frames.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        system_prompt: str = "You are a helpful voice assistant.",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ):
        super().__init__("openai-llm")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._messages: list[dict] = []
        self._tools: list[dict] = []
        self._gen_task = None

    def set_tools(self, tools: list[dict]) -> None:
        """Set available tools for function calling."""
        self._tools = tools

    async def process_frame(self, frame: Frame) -> None:
        import asyncio

        if frame.type == FrameType.CALL_START:
            # Initialize conversation with system prompt
            self._messages = [{"role": "system", "content": self.system_prompt}]
            # Inject initial context if provided
            context = frame.data or {}
            if context:
                context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
                self._messages.append({
                    "role": "system",
                    "content": f"Call context:\n{context_str}",
                })
            await self.emit(frame)

        elif frame.type == FrameType.STT_TRANSCRIPT:
            data = frame.data or {}
            if not data.get("is_final"):
                return  # Only process final transcripts
            text = data.get("text", "").strip()
            if not text:
                return
            self._messages.append({"role": "user", "content": text})
            
            # Cancel existing task on new input (barge-in or next user turn)
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
            # User interrupted agent - cancel current LLM generation task
            if self._gen_task and not self._gen_task.done():
                self._gen_task.cancel()
                logger.info("OpenAILLM: Canceled current active generation due to USER_SPEAKING")
            await self.emit(frame)

        elif frame.type == FrameType.CALL_END:
            if self._gen_task and not self._gen_task.done():
                self._gen_task.cancel()
            await self.emit(frame)

        else:
            await self.emit(frame)

    async def _generate(self) -> None:
        """Call OpenAI and stream the response."""
        kwargs: dict = {
            "model": self.model,
            "messages": self._messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        if self._tools:
            kwargs["tools"] = self._tools
            kwargs["tool_choice"] = "auto"

        full_text = ""
        tool_calls_raw: dict[int, dict] = {}

        try:
            stream = await self.client.chat.completions.create(**kwargs)
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                # Stream text tokens
                if delta.content:
                    full_text += delta.content
                    await self.emit(llm_text(delta.content))

                # Accumulate tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_raw:
                            tool_calls_raw[idx] = {
                                "id": tc.id or "",
                                "name": "",
                                "arguments": "",
                            }
                        if tc.id:
                            tool_calls_raw[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_raw[idx]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_raw[idx]["arguments"] += tc.function.arguments

        except Exception as e:
            logger.error(f"OpenAI LLM error: {e}")
            await self.emit(llm_text_complete("I'm sorry, I had a problem. Please try again."))
            return

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

        # Add assistant message to history
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

        await self.emit(llm_text_complete(full_text, tool_calls=tool_call_frames))
