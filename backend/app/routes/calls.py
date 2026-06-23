"""
Auris - Call routes
WebSocket endpoint for browser voice calls + REST for call history.
"""
import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.dependencies.auth import get_current_org, get_current_user
from app.models.agent import Agent
from app.models.call_run import CallRun
from app.models.organization import Organization
from app.models.user import User
from app.services.pipeline.factory import build_pipeline
from app.services.pipeline.transport.webrtc_transport import WebRTCTransport

router = APIRouter(prefix="/calls", tags=["calls"])


class CallRunResponse(BaseModel):
    id: int
    agent_id: int
    transport: str
    call_type: str
    status: str
    caller_number: str | None
    called_number: str | None
    duration_seconds: float | None
    disposition: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[CallRunResponse])
async def list_calls(
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    result = await db.execute(
        select(CallRun)
        .where(CallRun.org_id == org.id)
        .order_by(CallRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    runs = result.scalars().all()
    return [
        CallRunResponse(
            id=r.id, agent_id=r.agent_id, transport=r.transport,
            call_type=r.call_type, status=r.status,
            caller_number=r.caller_number, called_number=r.called_number,
            duration_seconds=r.duration_seconds, disposition=r.disposition,
            created_at=r.created_at.isoformat(),
        )
        for r in runs
    ]


@router.get("/{call_id}", response_model=CallRunResponse)
async def get_call(
    call_id: int,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CallRun).where(CallRun.id == call_id, CallRun.org_id == org.id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Call not found")
    return CallRunResponse(
        id=run.id, agent_id=run.agent_id, transport=run.transport,
        call_type=run.call_type, status=run.status,
        caller_number=run.caller_number, called_number=run.called_number,
        duration_seconds=run.duration_seconds, disposition=run.disposition,
        created_at=run.created_at.isoformat(),
    )


@router.websocket("/ws/{agent_id}")
async def websocket_call(
    websocket: WebSocket,
    agent_id: int,
    token: str,  # JWT passed as query param: /ws/123?token=xxx
):
    """
    WebSocket endpoint for browser voice calls.
    URL: /api/v1/calls/ws/{agent_id}?token=<jwt>

    Protocol:
      Browser sends: { "type": "start", "context": {...} }
      Then streams:  { "type": "audio", "data": "<base64 PCM 16kHz mono>" }
      To end:        { "type": "end" }

      Server sends:  { "type": "audio", "data": "<base64 PCM>" }
                     { "type": "transcript", "text": "...", "final": true }
                     { "type": "end" }
    """
    await websocket.accept()

    # Validate token + get agent
    from app.core.security import decode_access_token
    payload = decode_access_token(token)
    if not payload:
        await websocket.send_json({"type": "error", "message": "Unauthorized"})
        await websocket.close()
        return

    user_id = int(payload["sub"])
    org_id = payload.get("org")

    async with AsyncSessionLocal() as db:
        # Load agent
        result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()

        if not agent or (org_id and agent.org_id != org_id):
            await websocket.send_json({"type": "error", "message": "Agent not found"})
            await websocket.close()
            return

        # Create call run record
        run = CallRun(
            org_id=agent.org_id,
            agent_id=agent.id,
            transport="webrtc",
            call_type="inbound",
            status="running",
            started_at=datetime.now(UTC),
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        run_id = run.id

    logger.info(f"WebRTC call started: agent={agent_id} run={run_id}")

    # Build the pipeline
    # Extract system prompt from agent graph (first node or top-level prompt)
    system_prompt = _extract_system_prompt(agent.graph)
    language = agent.model_config.get("language", "en")

    pipeline = build_pipeline(
        model_config=agent.model_config,
        system_prompt=system_prompt,
        language=language,
    )

    transport = WebRTCTransport(
        ws=websocket,
        pipeline_push=pipeline.push,
        pipeline_collect=pipeline.collect,
    )

    start_time = datetime.now(UTC)

    try:
        await pipeline.start()
        await transport.run()
    except WebSocketDisconnect:
        logger.info(f"WebRTC call disconnected: run={run_id}")
    except Exception as e:
        logger.error(f"WebRTC call error: run={run_id} error={e}")
    finally:
        await pipeline.stop()
        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()

        # Update call run
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(CallRun).where(CallRun.id == run_id))
            run = result.scalar_one_or_none()
            if run:
                run.status = "completed"
                run.ended_at = end_time
                run.duration_seconds = duration
                await db.commit()

        logger.info(f"Call run {run_id} completed: {duration:.1f}s")


def _extract_system_prompt(graph: dict) -> str:
    """Extract the system prompt from an agent graph definition."""
    if not graph:
        return "You are a helpful voice assistant. Be concise and friendly."

    # Check for top-level system_prompt
    if "system_prompt" in graph:
        return graph["system_prompt"]

    # Check nodes for a 'start' node with a prompt
    nodes = graph.get("nodes", [])
    for node in nodes:
        if node.get("type") == "start" or node.get("id") == "start":
            return node.get("prompt", "You are a helpful voice assistant.")

    return "You are a helpful voice assistant. Be concise and friendly."
