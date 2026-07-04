"""
Auris - Retell Custom LLM WebSocket Processor
Connects to external custom LLM WebSocket servers using Retell AI's exact interactive protocol.
Written from scratch for 100% drop-in compatibility.
"""
import asyncio
import json
from loguru import logger
import websockets

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import (
    Frame, FrameType, llm_text, llm_text_complete, tool_call, error_frame
)


class RetellWebsocketLLM(BaseProcessor):
    """
    Acts as a WebSocket client to an external LLM server (like Retell AI custom LLM).
    Receives STT_TRANSCRIPT + TOOL_RESULT frames from Auris Pipecat pipeline.
    Sends Retell-formatted JSON requests: 'config', 'response_required', 'reminder_required', 'ping_pong'.
    Receives streaming text chunks and tool calls from the server, converting them to LLM_TEXT, LLM_TEXT_COMPLETE, and TOOL_CALL frames.
    """

    def __init__(
        self,
        websocket_url: str,
        model_config: dict | None = None,
        system_prompt: str = "You are a helpful voice assistant.",
        initial_message: str | None = None,
    ):
        super().__init__("retell-websocket-llm")
        self.websocket_url = websocket_url
        self.model_config = model_config or {}
        self.system_prompt = system_prompt
        self.initial_message = initial_message
        self._ws = None
        self._receive_task = None
        self._response_id = 0
        self._transcript: list[dict] = []
        self._current_call_id = "unknown"
        self._current_text_buffer = ""
        self._tools: list[dict] = []

    def set_tools(self, tools: list[dict]) -> None:
        """Set available tools for function calling."""
        self._tools = tools

    async def process_frame(self, frame: Frame) -> None:
        if frame.type == FrameType.CALL_START:
            data = frame.data or {}
            self._current_call_id = str(data.get("run_id", "1"))
            
            # Format target WebSocket URL
            target_url = self.websocket_url
            if "{call_id}" in target_url:
                target_url = target_url.replace("{call_id}", self._current_call_id)
            elif not target_url.endswith(self._current_call_id) and "/llm-websocket" in target_url:
                target_url = f"{target_url.rstrip('/')}/{self._current_call_id}"

            # Initialize transcript with system prompt
            self._transcript = [{"role": "system", "content": self.system_prompt}]
            context_vars = {k: v for k, v in data.items() if k not in ("run_id", "call_type")}
            if context_vars:
                context_str = "\n".join(f"{k}: {v}" for k, v in context_vars.items())
                self._transcript.append({
                    "role": "system",
                    "content": f"Call context:\n{context_str}"
                })

            # Connect to external WebSocket server
            try:
                custom_headers = self.model_config.get("custom_headers", {})
                custom_headers["X-Auris-Call-Id"] = self._current_call_id
                
                logger.info(f"RetellWebsocketLLM: Connecting to {target_url}")
                self._ws = await websockets.connect(target_url, extra_headers=custom_headers)
                
                # Send Retell config packet
                await self._ws.send(json.dumps({
                    "response_type": "config",
                    "config": {
                        "auto_reconnect": True,
                        "call_details": True,
                    },
                    "response_id": 1,
                }))
                
                # Start listening loop
                self._receive_task = asyncio.create_task(self._receive_loop())
                
                # If outbound call or initial message, send begin trigger
                if self.initial_message or data.get("call_type") == "outbound":
                    msg = self.initial_message or "Hello"
                    self._transcript.append({"role": "user", "content": msg})
                    self._response_id += 1
                    await self._send_response_required()

            except Exception as e:
                logger.error(f"RetellWebsocketLLM failed to connect to {target_url}: {e}")
                await self.emit(error_frame(f"Retell WebSocket Connection Error: {e}"))

            await self.emit(frame)

        elif frame.type == FrameType.STT_TRANSCRIPT:
            data = frame.data or {}
            if not data.get("is_final"):
                return
            text = data.get("text", "").strip()
            if not text:
                return
            
            self._transcript.append({"role": "user", "content": text})
            self._response_id += 1
            await self._send_response_required()
            await self.emit(frame)

        elif frame.type == FrameType.TOOL_RESULT:
            data = frame.data or {}
            self._transcript.append({
                "role": "tool",
                "tool_call_id": data["call_id"],
                "content": json.dumps(data["result"])
            })
            self._response_id += 1
            await self._send_response_required()

        elif frame.type == FrameType.USER_SPEAKING:
            # Interruption - signal if needed
            await self.emit(frame)

        elif frame.type == FrameType.CALL_END:
            await self._cleanup()
            await self.emit(frame)

        else:
            await self.emit(frame)

    async def _send_response_required(self) -> None:
        """Send response_required payload to the external LLM WebSocket."""
        if not self._ws:
            return
        try:
            payload = {
                "interaction_type": "response_required",
                "response_id": self._response_id,
                "transcript": self._transcript,
            }
            await self._ws.send(json.dumps(payload, ensure_ascii=False))
            self._current_text_buffer = ""
        except Exception as e:
            logger.error(f"RetellWebsocketLLM error sending response_required: {e}")

    async def _receive_loop(self) -> None:
        """Listen for messages from the external Retell LLM WebSocket server."""
        try:
            while self._ws:
                msg = await self._ws.recv()
                if not msg:
                    continue
                try:
                    data = json.loads(msg)
                except json.JSONDecodeError:
                    continue

                response_type = data.get("response_type") or data.get("event_type")
                
                # Handle Ping Pong
                if response_type == "ping_pong" or data.get("interaction_type") == "ping_pong":
                    pong_payload = {
                        "response_type": "ping_pong",
                        "timestamp": data.get("timestamp"),
                    }
                    await self._ws.send(json.dumps(pong_payload))
                    continue

                # Handle Text Responses / Chunks
                if response_type in ("response", "agent_response", "chunk", "config"):
                    content = data.get("content", "")
                    content_complete = data.get("content_complete", False)
                    
                    if content:
                        self._current_text_buffer += content
                        await self.emit(llm_text(content))
                    
                    if content_complete:
                        complete_text = self._current_text_buffer.strip()
                        self._transcript.append({"role": "assistant", "content": complete_text})
                        await self.emit(llm_text_complete(complete_text))
                        self._current_text_buffer = ""

                # Handle Tool Calls
                tool_calls = data.get("tool_calls") or (data.get("tool_call") and [data["tool_call"]])
                if tool_calls:
                    for tc in tool_calls:
                        call_id = tc.get("id") or tc.get("call_id") or "call_1"
                        name = tc.get("name") or (tc.get("function", {}).get("name"))
                        args = tc.get("arguments") or (tc.get("function", {}).get("arguments", {}))
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                args = {}
                        if name:
                            await self.emit(tool_call(name=name, arguments=args, call_id=call_id))

                # Handle Call End / Transfer commands from external server
                if response_type == "end_call" or data.get("end_call"):
                    await self.emit(Frame(type=FrameType.CALL_END))
                elif response_type == "transfer_call" or data.get("transfer_call"):
                    target_id = data.get("target_agent_id")
                    if target_id:
                        await self.emit(tool_call(
                            name="transfer_to_agent",
                            arguments={"target_agent_id": int(target_id)},
                            call_id="transfer_ws"
                        ))

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"RetellWebsocketLLM connection closed for call {self._current_call_id}")
        except Exception as e:
            logger.error(f"RetellWebsocketLLM receive loop error: {e}")
        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
