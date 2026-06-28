"""
Auris - Live Monitor Tracker
Maintains active call state in memory and broadcasts updates to monitoring WebSockets.
"""
from typing import Dict, Any, Set
import time
import asyncio
from fastapi import WebSocket
from loguru import logger

class MonitorTracker:
    active_calls: Dict[int, Dict[str, Any]] = {}
    listeners: Set[WebSocket] = set()

    @classmethod
    def register_call(cls, run_id: int, agent_id: int, agent_name: str, transport: str, call_type: str, caller_number: str | None, called_number: str | None):
        cls.active_calls[run_id] = {
            "run_id": run_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "transport": transport,
            "call_type": call_type,
            "caller_number": caller_number or "Anonymous",
            "called_number": called_number or "Auris Sandbox",
            "started_at": time.time(),
            "last_transcript": "",
            "status": "running"
        }
        cls.broadcast({"type": "call_started", "call": cls.active_calls[run_id]})

    @classmethod
    def update_transcript(cls, run_id: int, text: str, sender: str):
        if run_id in cls.active_calls:
            cls.active_calls[run_id]["last_transcript"] = f"{sender.capitalize()}: {text}"
            cls.broadcast({
                "type": "call_updated",
                "run_id": run_id,
                "last_transcript": cls.active_calls[run_id]["last_transcript"]
            })

    @classmethod
    def end_call(cls, run_id: int):
        if run_id in cls.active_calls:
            call = cls.active_calls.pop(run_id)
            cls.broadcast({"type": "call_ended", "run_id": run_id})

    @classmethod
    def add_listener(cls, websocket: WebSocket):
        cls.listeners.add(websocket)
        # Immediately send list of active calls to the new listener
        return list(cls.active_calls.values())

    @classmethod
    def remove_listener(cls, websocket: WebSocket):
        cls.listeners.discard(websocket)

    @classmethod
    def broadcast(cls, message: Dict[str, Any]):
        if not cls.listeners:
            return

        # Run broadcasts concurrently inside the running event loop.
        # get_event_loop() works here because this method is always called
        # from within an async context (route handlers / websocket handlers).
        async def send_to_all():
            disconnected = []
            for ws in list(cls.listeners):
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(ws)
            for ws in disconnected:
                cls.listeners.discard(ws)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(send_to_all())
        except Exception as e:
            logger.debug(f"MonitorTracker.broadcast skipped (no event loop): {e}")
