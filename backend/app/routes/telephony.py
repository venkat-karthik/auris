from fastapi import APIRouter, WebSocket, Query, HTTPException, Depends
from app.dependencies.auth import get_current_user, get_current_org
from app.services.pipeline.transport.telnyx_transport import TelnyxTransport
from app.services.pipeline.factory import build_pipeline
import asyncio
from app.services.pipeline.frame import audio_in, FrameType
from app.models.agent import Agent
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db

router = APIRouter()

@router.websocket("/telephony/ws/telnyx")
async def telnyx_ws(
    websocket: WebSocket,
    call_control_id: str = Query(..., description="Telnyx call control ID"),
    user=Depends(get_current_user),
    org=Depends(get_current_org),
    db: Session = Depends(get_db),
):
    await websocket.accept()
    # Retrieve the agent for this organization (fallback to first)
    result = await db.execute(select(Agent).where(Agent.org_id == org.id))
    agent = result.scalars().first()
    if not agent:
        await websocket.close(code=1008)
        raise HTTPException(status_code=404, detail="Agent not found for organization")
    # Build pipeline based on agent config
    pipeline = build_pipeline(agent.model_config, system_prompt=agent.description or "", language="en")
    await pipeline.start()
    try:
        async for pcm_chunk in TelnyxTransport.receive_ulaw(websocket):
            # Push incoming audio into pipeline
            await pipeline.push(audio_in(pcm_chunk))
            # Collect any output frame (blocking until available)
            out_frame = await pipeline.collect()
            if out_frame and out_frame.type == FrameType.AUDIO_OUT:
                await TelnyxTransport.send_pcm(websocket, out_frame.data)
    finally:
        await pipeline.stop()


@router.post("/telephony/inbound/telnyx")
async def inbound_telnyx(
    call_control_id: str = Query(...),
    org=Depends(get_current_org),
    user=Depends(get_current_user),
):
    # Placeholder: return TeXML that tells Telnyx to connect to the WS endpoint
    ws_url = f"wss://{org.id}.example.com/api/v1/telephony/ws/telnyx?call_control_id={call_control_id}"
    return {
        "texml": f"<Response><Connect><WebSocket url='{ws_url}'/></Connect></Response>"
    }
