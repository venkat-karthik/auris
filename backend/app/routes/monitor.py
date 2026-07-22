"""
Auris - Monitor routes
WebSocket endpoint for active call subscription updates.
Health monitoring and circuit breaker status.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from app.services.monitor_tracker import MonitorTracker
from app.services.circuit_breaker import get_all_circuit_breakers

router = APIRouter(prefix="/monitor", tags=["monitor"])

@router.get("/circuit-breakers")
async def get_circuit_breaker_status():
    """Get status of all circuit breakers for external API calls."""
    return {
        "circuit_breakers": get_all_circuit_breakers(),
        "total": len(get_all_circuit_breakers())
    }


@router.websocket("/ws")
async def monitor_ws(websocket: WebSocket):
    await websocket.accept()
    logger.info("New monitor client subscribed")
    active_calls = MonitorTracker.add_listener(websocket)
    try:
        # Send initial list of active calls
        await websocket.send_json({"type": "init", "calls": active_calls})
        import asyncio
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send a ping message to detect client silent disconnection
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        logger.info("Monitor client unsubscribed")
    except Exception as e:
        logger.error(f"Monitor websocket error: {e}")
    finally:
        MonitorTracker.remove_listener(websocket)
