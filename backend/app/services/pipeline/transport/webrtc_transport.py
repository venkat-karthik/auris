"""
Auris - WebRTC Transport
Handles browser-based voice calls via WebSocket signaling + audio.
Written from scratch — no aiortc or pipecat dependency.
"""
import asyncio
import json
from loguru import logger
from fastapi import WebSocket, WebSocketDisconnect

from app.services.pipeline.frame import Frame, FrameType, audio_in, call_end, call_start


class WebRTCTransport:
    """
    Bridges a browser WebSocket connection to the Auris pipeline.

    Protocol (JSON messages over WebSocket):
      Browser → Server:
        { "type": "start", "context": {...} }   — call started
        { "type": "audio", "data": "<base64 PCM>" }  — audio chunk
        { "type": "end" }                         — call ended

      Server → Browser:
        { "type": "audio", "data": "<base64 PCM>" }  — TTS audio
        { "type": "transcript", "text": "...", "final": true }
        { "type": "end" }
    """

    def __init__(self, ws: WebSocket, pipeline_push, pipeline_collect):
        self.ws = ws
        self._push = pipeline_push      # async fn to push frames into pipeline
        self._collect = pipeline_collect  # async fn to get frames from pipeline

    async def run(self) -> None:
        """Run receive and send loops concurrently."""
        await asyncio.gather(
            self._receive_loop(),
            self._send_loop(),
        )

    async def _receive_loop(self) -> None:
        """Read from browser WebSocket → push into pipeline."""
        import base64
        try:
            async for raw in self.ws.iter_text():
                msg = json.loads(raw)
                msg_type = msg.get("type")

                if msg_type == "start":
                    context = msg.get("context", {})
                    await self._push(call_start(context))
                    logger.info("WebRTC call started")

                elif msg_type == "audio":
                    pcm = base64.b64decode(msg["data"])
                    await self._push(audio_in(pcm))

                elif msg_type == "end":
                    await self._push(call_end("user_hangup"))
                    break

        except WebSocketDisconnect:
            await self._push(call_end("disconnect"))
        except Exception as e:
            logger.error(f"WebRTC receive error: {e}")
            await self._push(call_end("error"))

    async def _send_loop(self) -> None:
        """Read from pipeline output → send to browser."""
        import base64
        while True:
            frame = await self._collect()
            if frame is None:
                await self.ws.send_json({"type": "end"})
                break

            if frame.type == FrameType.AUDIO_OUT:
                await self.ws.send_json({
                    "type": "audio",
                    "data": base64.b64encode(frame.data).decode(),
                })

            elif frame.type == FrameType.STT_TRANSCRIPT:
                data = frame.data or {}
                await self.ws.send_json({
                    "type": "transcript",
                    "text": data.get("text", ""),
                    "final": data.get("is_final", False),
                })

            elif frame.type == FrameType.USER_SPEAKING:
                await self.ws.send_json({
                    "type": "interrupted"
                })

            elif frame.type == FrameType.CALL_END:
                await self.ws.send_json({"type": "end"})
                break
