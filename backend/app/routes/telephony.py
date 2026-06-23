from fastapi import APIRouter, WebSocket, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from app.services.pipeline.transport.telnyx_transport import TelnyxTransport
from app.services.pipeline.factory import build_pipeline
from app.services.pipeline.frame import audio_in, FrameType
from app.models.agent import Agent
from app.core.database import get_db

router = APIRouter()

@router.websocket("/telephony/ws/telnyx")
async def telnyx_ws(
    websocket: WebSocket,
    call_control_id: str = Query(..., description="Telnyx call control ID"),
    org_id: int = Query(..., description="Organization ID"),
    agent_id: int = Query(..., description="Agent ID"),
    db: AsyncSession = Depends(get_db),
):
    await websocket.accept()
    # Retrieve the agent for this organization
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id)
    )
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
    org_id: int = Query(...),
    agent_id: int = Query(...),
):
    ws_url = f"wss://api.example.com/api/v1/telephony/ws/telnyx?call_control_id={call_control_id}&org_id={org_id}&agent_id={agent_id}"
    return {
        "texml": f"<Response><Connect><WebSocket url='{ws_url}'/></Connect></Response>"
    }

