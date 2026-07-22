"""
Auris - Call routes
WebSocket endpoint for browser voice calls + REST for call history.
Refactored to use CRUD helpers for consistency and reduced duplication.
"""
import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from loguru import logger
from fastapi.responses import FileResponse

from pydantic import BaseModel
import os
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.core.config import RECORDINGS_DIR
from app.services.transfer_manager import warm_transfer
from app.dependencies.auth import get_current_org, get_current_user
from app.models.agent import Agent
from app.models.call_run import CallRun
from app.models.organization import Organization
from app.models.user import User
from app.services.pipeline.factory import build_pipeline
from app.services.pipeline.transport.webrtc_transport import WebRTCTransport
from app.utils.crud import (
    get_agent_or_404,
    get_call_or_404,
    list_calls_paginated,
    safe_add_and_commit,
    safe_update_and_commit,
)

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
    voicemail: bool | None
    summary: str | None = None
    sentiment: str | None = None
    key_topics: list[str] | None = None
    task_completed: bool | None = None
    usage_stats: dict | None = None
    recording_path: str | None = None
    transcript_path: str | None = None
    created_at: str

    class Config:
        from_attributes = True


class CallAnalysisResponse(BaseModel):
    call_id: int
    summary: str | None
    sentiment: str | None
    key_topics: list[str] | None
    task_completed: bool | None
    disposition: str | None

class WarmTransferRequest(BaseModel):
    target_agent_id: int
    whisper_url: Optional[str] = None

class DispatchCallRequest(BaseModel):
    agent_id: int
    customer_number: str
    custom_data: dict | None = None

class WebCallRequest(BaseModel):
    agent_id: int
    metadata: dict | None = None
    caller_number: str | None = "Browser WebRTC Client"


@router.post("/dispatch")
async def dispatch_call(
    req: DispatchCallRequest,
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dispatch an outbound voice call via Telnyx/Twilio."""
    agent = await get_agent_or_404(req.agent_id, org.id, db, eager_load=False)

    call_run = CallRun(
        org_id=org.id,
        agent_id=agent.id,
        caller_number=req.customer_number,
        transport="telnyx",
        call_type="outbound",
        status="initiated",
        initial_context=req.custom_data or {},
    )
    call_run = await safe_add_and_commit(db, call_run, "dispatch_call")
    return {"status": "dispatched", "call_run_id": call_run.id, "customer_number": req.customer_number}


@router.post("/web-call")
async def create_web_call(
    req: WebCallRequest,
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a live WebRTC voice session."""
    from app.services.structured_logging import log_call_created
    
    agent = await get_agent_or_404(req.agent_id, org.id, db, eager_load=False)

    from app.core.security import create_access_token
    from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
    from datetime import timedelta
    access_token = create_access_token(
        data={"sub": str(user.id), "org": org.id, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    call_run = CallRun(
        org_id=org.id,
        agent_id=agent.id,
        caller_number=req.caller_number or "Browser WebRTC Client",
        transport="webrtc",
        call_type="inbound",
        status="initiated",
        initial_context=req.metadata or {},
        started_at=datetime.now(UTC),
    )
    call_run = await safe_add_and_commit(db, call_run, "create_web_call")
    
    log_call_created(
        call_id=call_run.id,
        org_id=org.id,
        agent_id=agent.id,
        call_type="webrtc",
        caller_number=call_run.caller_number
    )

    return {
        "call_id": call_run.id,
        "access_token": access_token,
        "webrtc_url": f"/api/v1/calls/ws/{agent.id}?token={access_token}&caller_number=Browser%20WebRTC"
    }


@router.post("/{call_id}/end")
async def end_call(
    call_id: int,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """End a call run."""
    run = await get_call_or_404(call_id, org.id, db)
    if run.status in ("initiated", "running"):
        run.status = "completed"
        run.ended_at = datetime.now(UTC)
        if run.started_at:
            run.duration_seconds = (run.ended_at - run.started_at).total_seconds()
        await safe_update_and_commit(db, run, "end_call")
    return {"status": "ended", "call_id": run.id}


@router.get("", response_model=list[CallRunResponse])
async def list_calls(
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    agent_id: Optional[int] = None,
    status: Optional[str] = None,
    call_type: Optional[str] = None,
    disposition: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    List calls with filtering and pagination.
    
    Query parameters:
    - limit: Page size (default: 50)
    - offset: Pagination offset (default: 0)
    - agent_id: Filter by agent
    - status: Filter by status (initiated, running, completed, failed)
    - call_type: Filter by type (inbound, outbound)
    - disposition: Filter by disposition
    - start_date: Filter calls created after this date
    - end_date: Filter calls created before this date
    
    Response includes X-Request-ID header for request tracing.
    """
    from sqlalchemy.orm import selectinload
    
    query = (
        select(CallRun)
        .where(CallRun.org_id == org.id)
        .options(selectinload(CallRun.agent), selectinload(CallRun.org))
    )
    
    # Dynamic filtering
    if agent_id is not None:
        query = query.where(CallRun.agent_id == agent_id)
    if status is not None:
        query = query.where(CallRun.status == status)
    if call_type is not None:
        query = query.where(CallRun.call_type == call_type)
    if disposition is not None:
        query = query.where(CallRun.disposition == disposition)
    if start_date is not None:
        query = query.where(CallRun.created_at >= start_date)
    if end_date is not None:
        query = query.where(CallRun.created_at <= end_date)

    query = query.order_by(CallRun.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    runs = result.scalars().all()
    
    return [
        CallRunResponse(
            id=r.id,
            agent_id=r.agent_id,
            transport=r.transport,
            call_type=r.call_type,
            status=r.status,
            caller_number=r.caller_number,
            called_number=r.called_number,
            duration_seconds=r.duration_seconds,
            disposition=r.disposition,
            voicemail=(r.voicemail == "true") if r.voicemail is not None else None,
            summary=r.summary,
            sentiment=r.sentiment,
            key_topics=r.key_topics,
            task_completed=r.task_completed,
            usage_stats=r.usage_stats,
            recording_path=r.recording_path,
            transcript_path=r.transcript_path,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in runs
    ]


@router.get("/{call_id}", response_model=CallRunResponse)
async def get_call(
    call_id: int,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific call run."""
    run = await get_call_or_404(call_id, org.id, db)
    return CallRunResponse(
        id=run.id,
        agent_id=run.agent_id,
        transport=run.transport,
        call_type=run.call_type,
        status=run.status,
        caller_number=run.caller_number,
        called_number=run.called_number,
        duration_seconds=run.duration_seconds,
        disposition=run.disposition,
        voicemail=(run.voicemail == "true") if run.voicemail is not None else None,
        summary=run.summary,
        sentiment=run.sentiment,
        key_topics=run.key_topics,
        task_completed=run.task_completed,
        usage_stats=run.usage_stats,
        recording_path=run.recording_path,
        transcript_path=run.transcript_path,
        created_at=run.created_at.isoformat() if run.created_at else None,
    )


@router.get("/{call_id}/analysis", response_model=CallAnalysisResponse)
async def get_call_analysis(
    call_id: int,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve only the structured post-call analysis fields for a call run."""
    run = await get_call_or_404(call_id, org.id, db)
    return CallAnalysisResponse(
        call_id=run.id,
        summary=run.summary,
        sentiment=run.sentiment,
        key_topics=run.key_topics,
        task_completed=run.task_completed,
        disposition=run.disposition,
    )


@router.get("/turn-credentials")
async def get_turn_credentials(user = Depends(get_current_user)):
    # Generate HMAC-based time-limited TURN credentials
    import hmac, hashlib, time, base64
    from app.core.config import TURN_SECRET, TURN_HOST, TURN_PORT
    username = f"{int(time.time()) + 3600}:{user.id}"
    password = base64.b64encode(
        hmac.new(TURN_SECRET.encode(), username.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "urls": [f"turn:{TURN_HOST}:{TURN_PORT}"],
        "username": username,
        "credential": password
    }


@router.websocket("/ws/{agent_id}")
async def websocket_call(
    websocket: WebSocket,
    agent_id: int,
    token: str,  # JWT passed as query param: /ws/123?token=xxx
    caller_number: str | None = None,
    called_number: str | None = None,
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

        # Check organization credit balance
        org_result = await db.execute(
            select(Organization).where(Organization.id == agent.org_id)
        )
        org = org_result.scalar_one_or_none()
        if not org or (org.balance_credits or 0.0) <= 0.0:
            await websocket.send_json({"type": "error", "message": "Insufficient credit balance. Please recharge."})
            await websocket.close(code=4002)
            return

        # Look up repeat caller info for prompt injection
        from app.services.customer_memory import lookup_customer
        customer_context = await lookup_customer(db, agent.org_id, caller_number)

        # Create call run record
        run = CallRun(
            org_id=agent.org_id,
            agent_id=agent.id,
            transport="webrtc",
            call_type="inbound",
            status="running",
            caller_number=caller_number,
            called_number=called_number,
            started_at=datetime.now(UTC),
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        run_id = run.id

        # Trigger call.started webhook event
        from app.services.webhook_dispatcher import dispatch_call_webhook
        asyncio.create_task(dispatch_call_webhook(db, run_id, "call.started"))

        from app.services.monitor_tracker import MonitorTracker
        MonitorTracker.register_call(
            run_id=run_id,
            agent_id=agent.id,
            agent_name=agent.name,
            transport="webrtc",
            call_type="inbound",
            caller_number=caller_number,
            called_number=called_number
        )

    logger.info(f"WebRTC call started: agent={agent_id} run={run_id}")

    # Extract system prompt from agent graph (first node or top-level prompt)
    has_visual_nodes = len(agent.graph.get("nodes", [])) > 0
    workflow_state = None
    if has_visual_nodes:
        from app.services.pipeline.workflow_engine import WorkflowState
        workflow_state = WorkflowState(agent.graph, context_variables=agent.context_variables)
        system_prompt, should_end = await workflow_state.execute_active_node(db=db, run_id=run_id)
        if should_end:
            await websocket.send_json({"type": "end"})
            await websocket.close()
            return
    else:
        system_prompt = _extract_system_prompt(agent.graph)
        
        # A/B variant traffic splitting
        variants = agent.model_config.get("variants", [])
        if variants:
            import random
            total_weight = sum(v.get("traffic_weight", 0.0) for v in variants)
            if total_weight > 0:
                r = random.uniform(0, total_weight)
                curr_w = 0.0
                for v in variants:
                    curr_w += v.get("traffic_weight", 0.0)
                    if r <= curr_w:
                        system_prompt = v.get("system_prompt", system_prompt)
                        break

    if customer_context:
        system_prompt += customer_context
    language = agent.model_config.get("language", "en")

    pipeline = build_pipeline(
        model_config=agent.model_config,
        system_prompt=system_prompt,
        language=language,
    )

    # Find LLM processor and register tools
    llm_processor = None
    for p in pipeline.processors:
        if p.name in ("openai-llm", "groq-llm", "anthropic-llm"):
            llm_processor = p
            break

    from app.services.pipeline import ToolOrchestrator
    await ToolOrchestrator.register_agent_tools(agent, workflow_state, llm_processor)


    from app.services.pipeline.frame import FrameType, Frame
    transcript_segments = []
    recorded_audio_chunks = []
    import time
    
    # Latency tracking variables
    turn_timers = {
        "user_silent_at": None,
        "stt_done_at": None,
        "llm_start_at": None,
        "llm_done_at": None,
        "tts_start_at": None
    }
    usage_stats = {
        "llm_input_tokens": 0,
        "llm_output_tokens": 0,
        "stt_duration_ms": 0.0,
        "tts_duration_ms": 0.0,
        "latencies": []
    }

    async def collecting_wrapper():
        frame = await pipeline.collect()
        if frame:
            # Latency and usage accumulation
            if frame.type == FrameType.USER_SILENT:
                turn_timers["user_silent_at"] = time.time()
                
            elif frame.type == FrameType.STT_TRANSCRIPT:
                dur = frame.metadata.get("duration_ms", 0.0)
                usage_stats["stt_duration_ms"] += dur
                
                data = frame.data or {}
                if data.get("is_final"):
                    text = data.get("text", "").strip()
                    if text:
                        transcript_segments.append(f"User: {text}")
                        from app.services.monitor_tracker import MonitorTracker
                        MonitorTracker.update_transcript(run_id, text, "user")
                        
                        now = time.time()
                        turn_timers["stt_done_at"] = now
                        if turn_timers["user_silent_at"]:
                            stt_latency = (now - turn_timers["user_silent_at"]) * 1000.0
                            usage_stats["latencies"].append({"event": "stt", "ms": stt_latency})
                            
            elif frame.type == FrameType.LLM_TEXT:
                if not turn_timers["llm_start_at"]:
                    now = time.time()
                    turn_timers["llm_start_at"] = now
                    if turn_timers["stt_done_at"]:
                        llm_ttfb = (now - turn_timers["stt_done_at"]) * 1000.0
                        usage_stats["latencies"].append({"event": "llm_ttfb", "ms": llm_ttfb})
                        
            elif frame.type == FrameType.LLM_TEXT_COMPLETE:
                turn_timers["llm_done_at"] = time.time()
                
                usage = frame.metadata.get("usage", {})
                usage_stats["llm_input_tokens"] += usage.get("input_tokens", 0)
                usage_stats["llm_output_tokens"] += usage.get("output_tokens", 0)
                
                data = frame.data or {}
                text = data.get("text", "").strip()
                if text:
                    transcript_segments.append(f"Agent: {text}")
                    from app.services.monitor_tracker import MonitorTracker
                    MonitorTracker.update_transcript(run_id, text, "agent")
                    
            elif frame.type == FrameType.AUDIO_OUT:
                recorded_audio_chunks.append(frame.data)
                
                dur = frame.metadata.get("duration_ms", 0.0)
                usage_stats["tts_duration_ms"] += dur
                
                if turn_timers["llm_done_at"] and not turn_timers["tts_start_at"]:
                    now = time.time()
                    turn_timers["tts_start_at"] = now
                    tts_latency = (now - turn_timers["llm_done_at"]) * 1000.0
                    usage_stats["latencies"].append({"event": "tts", "ms": tts_latency})
                    
                    # Reset timers for next turn
                    for k in turn_timers:
                        turn_timers[k] = None

            elif frame.type == FrameType.TOOL_CALL:
                from app.services.pipeline import ToolOrchestrator
                await ToolOrchestrator.handle_tool_call(
                    frame=frame,
                    agent=agent,
                    run_id=run_id,
                    pipeline=pipeline,
                    llm_processor=llm_processor,
                    workflow_state=workflow_state,
                    caller_number=caller_number,
                    transcript_segments=transcript_segments,
                    db=db,
                )
        return frame


    transport = WebRTCTransport(
        ws=websocket,
        pipeline_push=pipeline.push,
        pipeline_collect=collecting_wrapper,
        run_id=run_id,
    )

    start_time = datetime.now(UTC)

    # Start credit monitor loop in background
    cost_tier = agent.model_config.get("cost_tier", "standard")
    monitor_task = asyncio.create_task(
        credit_monitor_loop(run_id, agent.org_id, cost_tier, pipeline, websocket)
    )

    # Start Redis Pub/Sub link click event listener task
    from app.dependencies.rate_limit import redis_client
    event_listener_task = None

    async def listen_redis_events():
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(
                f"call:link_clicks:{run_id}",
                f"call:coaching:{run_id}",
                f"call:audio:supervisor:{run_id}"
            )
            async for message in pubsub.listen():
                if message["type"] == "message":
                    event_data = json.loads(message["data"])
                    channel = message["channel"]

                    if "link_clicks" in channel:
                        if event_data.get("event") == "link_clicked":
                            click_url = event_data.get("url", "")
                            logger.info(f"Redis link click pub/sub event received for call {run_id}: {click_url}")
                            await pipeline.push(Frame(
                                type=FrameType.STT_TRANSCRIPT,
                                data={"text": f"[SYSTEM NOTICE: Customer clicked the link: {click_url}]", "is_final": True}
                            ))
                    elif "coaching" in channel:
                        instruction = event_data.get("instruction")
                        if instruction:
                            logger.info(f"Redis whisper coaching instruction received for call {run_id}: {instruction}")
                            await pipeline.push(Frame(
                                type=FrameType.STT_TRANSCRIPT,
                                data={"text": f"[SYSTEM NOTICE: Supervisor guidance - {instruction}]", "is_final": True}
                            ))
                    elif "audio:supervisor" in channel:
                        audio_b64 = event_data.get("data")
                        try:
                            is_takeover = await redis_client.get(f"call_takeover:{run_id}")
                        except Exception:
                            is_takeover = False
                        if is_takeover and audio_b64:
                            await websocket.send_json({"type": "audio", "data": audio_b64})
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Redis event listener offline: {e}")
        finally:
            try:
                if pubsub.connection:
                    await pubsub.unsubscribe()
            except Exception:
                pass

    event_listener_task = asyncio.create_task(listen_redis_events())

    try:
        await pipeline.start()
        # Push CALL_START to start the conversation pipeline
        await pipeline.push(Frame(type=FrameType.CALL_START, data={"run_id": run_id, "call_type": "inbound"}))
        await transport.run()
    except WebSocketDisconnect:
        logger.info(f"WebRTC call disconnected: run={run_id}")
    except Exception as e:
        logger.error(f"WebRTC call error: run={run_id} error={e}")
    finally:
        if event_listener_task:
            event_listener_task.cancel()
        monitor_task.cancel()
        try:
            await pipeline.stop()
        except Exception:
            pass
        from app.services.monitor_tracker import MonitorTracker
        MonitorTracker.end_call(run_id)
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
                
                # Upload transcript to MinIO/local fallback
                transcript_text = "\n".join(transcript_segments)
                if transcript_text:
                    try:
                        filename = f"transcripts/{run_id}.txt"
                        from app.tasks.worker import upload_file_to_minio
                        from app.core.config import MINIO_BUCKET
                        path = upload_file_to_minio(MINIO_BUCKET, filename, transcript_text.encode("utf-8"), "text/plain")
                        run.transcript_path = path
                    except Exception as e:
                        logger.error(f"Failed to upload transcript to MinIO: {e}")
                
                # Save WAV recording
                if recorded_audio_chunks:
                    try:
                        from app.routes.calls import pcm_to_wav
                        from app.tasks.worker import upload_file_to_minio
                        from app.core.config import MINIO_BUCKET
                        
                        pcm_data = b"".join(recorded_audio_chunks)
                        wav_data = pcm_to_wav(pcm_data)
                        rec_filename = f"recordings/{run_id}.wav"
                        rec_path = upload_file_to_minio(MINIO_BUCKET, rec_filename, wav_data, "audio/wav")
                        run.recording_path = rec_path
                    except Exception as e:
                        logger.error(f"Failed to upload recording to MinIO: {e}")
                
                # Save usage stats
                run.usage_stats = usage_stats
                await db.commit()
        
        await charge_final_credits(run_id, agent.org_id, duration, agent.model_config)

        # Enqueue background tasks on ARQ worker
        try:
            from arq import create_pool
            from arq.connections import RedisSettings
            from app.core.config import REDIS_URL
            redis_settings = RedisSettings.from_dsn(REDIS_URL)
            async def trigger_tasks():
                arq_pool = await create_pool(redis_settings)
                await arq_pool.enqueue_job("process_call_completion", run_id)
                await arq_pool.enqueue_job("update_customer_profile", run_id)
                await arq_pool.enqueue_job("run_post_call_analysis", run_id)
                await arq_pool.close()
            
            asyncio.create_task(trigger_tasks())
        except Exception as e:
            logger.error(f"Failed to enqueue ARQ background tasks: {e}")

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


@router.get("/{call_id}/transcript")
async def get_call_transcript(
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

    if not run.transcript_path:
        return {"id": call_id, "transcript": ""}

    try:
        from app.tasks.worker import download_file_from_minio
        from app.core.config import MINIO_BUCKET
        path = run.transcript_path
        if path.startswith(f"{MINIO_BUCKET}/"):
            path = path[len(f"{MINIO_BUCKET}/"):]
            
        transcript_bytes = download_file_from_minio(MINIO_BUCKET, path)
        transcript_text = transcript_bytes.decode("utf-8")
        return {"id": call_id, "transcript": transcript_text}
    except Exception as e:
        logger.error(f"Failed to read transcript file from {run.transcript_path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transcript file")

@router.post("/{call_id}/warm_transfer")
async def warm_transfer_endpoint(
    call_id: int,
    req: WarmTransferRequest,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    # Verify call belongs to organization
    result = await db.execute(select(CallRun).where(CallRun.id == call_id, CallRun.org_id == org.id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    success = await warm_transfer(call_id, req.target_agent_id, req.whisper_url)
    return {"success": success}

@router.post("/{call_id}/recording")
async def upload_recording(
    call_id: int,
    file: UploadFile = File(...),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CallRun).where(CallRun.id == call_id, CallRun.org_id == org.id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    filename = f"{call_id}_{file.filename}"
    file_path = os.path.join(RECORDINGS_DIR, filename)
    content = await file.read()
    with open(file_path, "wb") as out:
        out.write(content)
    call.recording_path = file_path
    await db.commit()
    return {"recording_path": file_path}

@router.get("/{call_id}/recording")
async def get_recording(
    call_id: int,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CallRun).where(CallRun.id == call_id, CallRun.org_id == org.id))
    call = result.scalar_one_or_none()
    if not call or not call.recording_path:
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(call.recording_path, media_type="audio/mpeg")


class DTMFRequest(BaseModel):
    digit: str


@router.post("/{call_id}/dtmf")
async def send_dtmf(
    call_id: int,
    req: DTMFRequest,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CallRun).where(CallRun.id == call_id, CallRun.org_id == org.id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    logger.info(f"Received DTMF digit '{req.digit}' for call run {call_id}")
    
    # Store digit sequence in gathered_context
    ctx = dict(call.gathered_context or {})
    ctx["dtmf_digits"] = ctx.get("dtmf_digits", "") + req.digit
    call.gathered_context = ctx
    await db.commit()
    
    return {"success": True, "digits": ctx["dtmf_digits"]}


async def credit_monitor_loop(run_id: int, org_id: int, cost_tier: str, pipeline, websocket):
    """
    Monitors the organization's credit balance in real-time.
    Checks and deducts credits every 10 seconds of active call.
    Deducts credits directly in the DB to prevent double-spending.
    Closes the pipeline and WebSocket if balance reaches 0.
    """
    if cost_tier == "economy":
        price_per_second = 0.0004  # $0.024/min
    elif cost_tier == "premium":
        price_per_second = 0.0016  # $0.096/min
    else:
        price_per_second = 0.0008  # $0.048/min (Standard)
        
    credits_per_second = price_per_second * 83.0  # 1 USD = 83 INR/credits
    interval = 10.0  # Check every 10 seconds
    credits_per_interval = credits_per_second * interval

    try:
        while True:
            await asyncio.sleep(interval)
            
            async with AsyncSessionLocal() as db:
                from app.models.organization import Organization
                org_result = await db.execute(
                    select(Organization).where(Organization.id == org_id)
                )
                org = org_result.scalar_one_or_none()
                if not org:
                    logger.error(f"Credit Monitor: Org {org_id} not found. Terminating call.")
                    break
                
                balance = org.balance_credits or 0.0
                if balance <= 0.0:
                    logger.warning(f"Credit Monitor: Org {org_id} balance is {balance}. Terminating call.")
                    from app.services.pipeline.frame import Frame, FrameType
                    await pipeline.push(Frame(type=FrameType.CALL_END))
                    try:
                        await websocket.close(code=4002)
                    except Exception:
                        pass
                    break
                
                deducted = min(balance, credits_per_interval)
                org.balance_credits = max(0.0, balance - deducted)
                logger.info(f"Credit Monitor: Deducted {deducted:.4f} credits from Org {org_id}. New balance: {org.balance_credits:.4f}")
                
                run_result = await db.execute(
                    select(CallRun).where(CallRun.id == run_id)
                )
                run = run_result.scalar_one_or_none()
                if run:
                    run.credits_used = (run.credits_used or 0.0) + deducted
                    run.cost_usd = (run.cost_usd or 0.0) + (deducted / 83.0)
                    db.add(run)
                
                db.add(org)
                await db.commit()
                
                if org.balance_credits <= 0.0:
                    logger.warning(f"Credit Monitor: Org {org_id} credits depleted. Terminating call.")
                    from app.services.pipeline.frame import Frame, FrameType
                    await pipeline.push(Frame(type=FrameType.CALL_END))
                    try:
                        await websocket.close(code=4002)
                    except Exception:
                        pass
                    break
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Credit Monitor error: {e}")


async def charge_final_credits(run_id: int, org_id: int, duration: float, agent_model_config: dict):
    """
    Deducts precise final credits based on call duration and cost tier.
    Used in finally blocks to ensure billing is updated immediately,
    independently of ARQ background task.
    """
    async with AsyncSessionLocal() as db_session:
        from app.models.organization import Organization
        from app.models.call_run import CallRun
        org_result = await db_session.execute(select(Organization).where(Organization.id == org_id))
        org_obj = org_result.scalar_one_or_none()
        if not org_obj:
            return
            
        price_per_second = org_obj.price_per_second_usd
        if price_per_second is None:
            cost_tier = agent_model_config.get("cost_tier", "standard")
            if cost_tier == "economy":
                price_per_second = 0.0004
            elif cost_tier == "premium":
                price_per_second = 0.0016
            else:
                price_per_second = 0.0008
                
        total_cost_usd = duration * price_per_second
        total_credits = total_cost_usd * 83.0
        
        run_res = await db_session.execute(select(CallRun).where(CallRun.id == run_id))
        run = run_res.scalar_one_or_none()
        if run:
            already_deducted = run.credits_used or 0.0
            credits_to_deduct = max(0.0, total_credits - already_deducted)
            
            org_obj.balance_credits = max(0.0, org_obj.balance_credits - credits_to_deduct)
            run.credits_used = total_credits
            run.cost_usd = total_cost_usd
            db_session.add(run)
            db_session.add(org_obj)
            await db_session.commit()
            logger.info(f"Credit Monitor: Charged final {credits_to_deduct:.4f} credits for call={run_id}. Total: {total_credits:.4f}, already_deducted: {already_deducted:.4f}, New balance: {org_obj.balance_credits:.4f}")


