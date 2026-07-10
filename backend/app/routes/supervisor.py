"""
Auris - Supervisor control router for Takeover and Whisper Coaching
"""
import asyncio
import json
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.dependencies.rate_limit import redis_client

router = APIRouter(prefix="/supervisor", tags=["supervisor"])


class WhisperRequest(BaseModel):
    call_run_id: int
    instruction: str


class TakeoverRequest(BaseModel):
    call_run_id: int


@router.post("/whisper")
async def whisper_coaching(req: WhisperRequest):
    """
    Endpoint for injecting a coaching hint into the running call pipeline.
    """
    channel = f"call:coaching:{req.call_run_id}"
    try:
        await redis_client.publish(channel, json.dumps({"instruction": req.instruction}))
        return {"status": "success", "message": "Instruction published"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/takeover/start")
async def takeover_start(req: TakeoverRequest):
    """
    Enables supervisor audio takeover mode.
    """
    key = f"call_takeover:{req.call_run_id}"
    channel = f"call:coaching:{req.call_run_id}"
    try:
        await redis_client.set(key, "true", ex=86400)
        await redis_client.publish(channel, json.dumps({"takeover": True}))
        return {"status": "success", "takeover": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/takeover/stop")
async def takeover_stop(req: TakeoverRequest):
    """
    Disables supervisor audio takeover mode.
    """
    key = f"call_takeover:{req.call_run_id}"
    channel = f"call:coaching:{req.call_run_id}"
    try:
        await redis_client.delete(key)
        await redis_client.publish(channel, json.dumps({"takeover": False}))
        return {"status": "success", "takeover": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/takeover/ws/{call_run_id}")
async def supervisor_takeover_ws(websocket: WebSocket, call_run_id: int):
    """
    WebSocket endpoint for supervisor browser audio streaming and takeover bridging.
    Sends incoming customer voice to supervisor, and routes supervisor mic audio to customer.
    """
    await websocket.accept()
    logger.info(f"Supervisor connected to takeover WS: call={call_run_id}")

    customer_audio_task = None

    async def listen_customer_audio():
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"call:audio:customer:{call_run_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    # Forward raw base64 or audio structure directly to supervisor console
                    data = json.loads(message["data"])
                    await websocket.send_json({
                        "type": "audio",
                        "data": data.get("data")
                    })
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in supervisor customer-audio subscriber: {e}")
        finally:
            await pubsub.unsubscribe()

    customer_audio_task = asyncio.create_task(listen_customer_audio())

    try:
        while True:
            # Listen to incoming supervisor console payloads (JSON with base64 audio data)
            msg = await websocket.receive_json()
            msg_type = msg.get("type")

            if msg_type == "audio":
                audio_b64 = msg.get("data", "")
                if audio_b64:
                    # Publish supervisor voice to the active call's supervisor audio channel
                    await redis_client.publish(
                        f"call:audio:supervisor:{call_run_id}",
                        json.dumps({"data": audio_b64})
                    )
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"Supervisor disconnected from takeover WS: call={call_run_id}")
    except Exception as e:
        logger.error(f"Supervisor takeover WS error: {e}")
    finally:
        if customer_audio_task:
            customer_audio_task.cancel()
