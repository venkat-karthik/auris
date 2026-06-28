"""
Auris - Monitor routes
WebSocket endpoint for active call subscription updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from app.services.monitor_tracker import MonitorTracker

router = APIRouter(prefix="/monitor", tags=["monitor"])

@router.websocket("/ws")
async def monitor_ws(websocket: WebSocket):
    await websocket.accept()
    logger.info("New monitor client subscribed")
    active_calls = MonitorTracker.add_listener(websocket)
    try:
        # Send initial list of active calls
        await websocket.send_json({"type": "init", "calls": active_calls})
        while True:
            # We don't expect messages from client, but we must read to detect disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Monitor client unsubscribed")
    except Exception as e:
        logger.error(f"Monitor websocket error: {e}")
    finally:
        MonitorTracker.remove_listener(websocket)
