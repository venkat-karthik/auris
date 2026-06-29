from fastapi import APIRouter, WebSocket, Query, HTTPException, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from sqlalchemy import select
import asyncio
import json
import base64
from datetime import UTC, datetime
from loguru import logger
import xml.sax.saxutils as saxutils
from urllib.parse import quote

from app.services.pipeline.transport.telnyx_transport import TelnyxTransport
from app.services.pipeline.transport.twilio_transport import TwilioTransport
from app.services.pipeline.factory import build_pipeline
from app.services.pipeline.frame import audio_in, FrameType
from app.models.agent import Agent
from app.models.call_run import CallRun
from app.core.database import get_db, AsyncSessionLocal

router = APIRouter()

@router.websocket("/telephony/ws/telnyx")
async def telnyx_ws(
    websocket: WebSocket,
    call_control_id: str = Query(..., description="Telnyx call control ID"),
    org_id: int = Query(..., description="Organization ID"),
    agent_id: int = Query(..., description="Agent ID"),
    from_number: str | None = Query(None, alias="from", description="Caller phone number"),
    to_number: str | None = Query(None, alias="to", description="Called phone number"),
    call_type: str = Query("inbound", description="Call type (inbound or outbound)"),
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
        return
    
    # Check organization credit balance
    from app.models.organization import Organization
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = org_result.scalar_one_or_none()
    if not org or (org.balance_credits or 0.0) <= 0.0:
        await websocket.close(code=4002)
        return
    
    # Look up repeat caller info for prompt injection
    from app.services.customer_memory import lookup_customer
    customer_context = await lookup_customer(db, org_id, from_number)
    
    # Create call run record
    run = CallRun(
        org_id=org_id,
        agent_id=agent.id,
        transport="telnyx",
        call_type=call_type,
        status="running",
        caller_number=from_number,
        called_number=to_number,
        started_at=datetime.now(UTC),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    run_id = run.id

    from app.services.monitor_tracker import MonitorTracker
    MonitorTracker.register_call(
        run_id=run_id,
        agent_id=agent.id,
        agent_name=agent.name,
        transport="telnyx",
        call_type=call_type,
        caller_number=from_number,
        called_number=to_number
    )

    has_visual_nodes = len(agent.graph.get("nodes", [])) > 0
    workflow_state = None
    if has_visual_nodes:
        from app.services.pipeline.workflow_engine import WorkflowState
        workflow_state = WorkflowState(agent.graph, context_variables=agent.context_variables)
        system_prompt, should_end = await workflow_state.execute_active_node()
        if should_end:
            await websocket.close(code=1000)
            return
    else:
        from app.routes.calls import _extract_system_prompt
        system_prompt = _extract_system_prompt(agent.graph)

    if customer_context:
        system_prompt += customer_context

    language = agent.model_config.get("language", "en")
    
    # Build pipeline based on agent config
    pipeline = build_pipeline(agent.model_config, system_prompt=system_prompt, language=language)

    # Find LLM processor and register tools
    llm_processor = None
    for p in pipeline.processors:
        if p.name in ("openai-llm", "groq-llm"):
            llm_processor = p
            break

    tools = []
    # Register search_knowledge_base if organization has documents
    async with AsyncSessionLocal() as session:
        from app.models.knowledge_base import KnowledgeBaseDocument
        doc_select = select(KnowledgeBaseDocument).where(
            KnowledgeBaseDocument.org_id == agent.org_id,
            (KnowledgeBaseDocument.agent_id == agent.id) | (KnowledgeBaseDocument.agent_id.is_(None))
        )
        doc_res = await session.execute(doc_select)
        has_docs = len(doc_res.scalars().all()) > 0

    if has_docs:
        tools.append({
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Search the knowledge base for documentation, guides, company policies to answer customer queries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search term or query containing relevant keywords."}
                    },
                    "required": ["query"]
                }
            }
        })

    if workflow_state:
        tools.append({
            "type": "function",
            "function": {
                "name": "submit_customer_answer",
                "description": "Submit a validated answer to the question asked, updating the context and transitioning call state.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string", "description": "The extracted value / answer from customer's speech."}
                    },
                    "required": ["value"]
                }
            }
        })
        tools.append({
            "type": "function",
            "function": {
                "name": "end_call",
                "description": "Terminate the call immediately.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        })

    if llm_processor and tools:
        llm_processor.set_tools(tools)
    
    transcript_segments = []

    async def collecting_wrapper():
        frame = await pipeline.collect()
        if frame:
            if frame.type == FrameType.STT_TRANSCRIPT:
                data = frame.data or {}
                if data.get("is_final"):
                    text = data.get("text", "").strip()
                    if text:
                        transcript_segments.append(f"User: {text}")
                        from app.services.monitor_tracker import MonitorTracker
                        MonitorTracker.update_transcript(run_id, text, "user")
            elif frame.type == FrameType.LLM_TEXT_COMPLETE:
                data = frame.data or {}
                text = data.get("text", "").strip()
                if text:
                    transcript_segments.append(f"Agent: {text}")
                    from app.services.monitor_tracker import MonitorTracker
                    MonitorTracker.update_transcript(run_id, text, "agent")
            elif frame.type == FrameType.TOOL_CALL:
                # Intercept tool calls, execute them, and push back TOOL_RESULT
                data = frame.data or {}
                name = data.get("name")
                args = data.get("arguments", {})
                call_id = data.get("call_id")
                result = None

                if name == "search_knowledge_base":
                    query = args.get("query", "")
                    async with AsyncSessionLocal() as session:
                        from app.services.rag_service import retrieve_context
                        result = await retrieve_context(session, agent.id, agent.org_id, query)
                elif name == "submit_customer_answer" and workflow_state:
                    val = args.get("value", "")
                    active_node = workflow_state.get_active_node()
                    if active_node and active_node.get("type") == "qa":
                        var_name = active_node.get("data", {}).get("expected_variable", "qa_ans")
                        workflow_state.context[var_name] = val
                    next_node = workflow_state.transition_to_next()
                    if next_node:
                        from app.services.pipeline.frame import Frame
                        new_prompt, should_end = await workflow_state.execute_active_node()
                        if should_end:
                            await pipeline.push(Frame(type=FrameType.CALL_END))
                            result = {"status": "call_ended"}
                        else:
                            if llm_processor:
                                llm_processor.system_prompt = new_prompt
                                llm_processor._messages.append({
                                    "role": "system",
                                    "content": f"[SYSTEM NOTICE: Workflow state changed. Active Prompt is now:\n{new_prompt}]"
                                })
                            result = {"status": "success", "next_node": next_node.get("id")}
                    else:
                        result = {"status": "success", "next_node": None}
                elif name == "end_call":
                    from app.services.pipeline.frame import Frame
                    await pipeline.push(Frame(type=FrameType.CALL_END))
                    result = {"status": "call_ended"}

                if result is not None:
                    from app.services.pipeline.frame import Frame
                    await pipeline.push(Frame(type=FrameType.TOOL_RESULT, data={"call_id": call_id, "result": result}))
        return frame

    start_time = datetime.now(UTC)

    # Start credit monitor loop in background
    cost_tier = agent.model_config.get("cost_tier", "standard")
    from app.routes.calls import credit_monitor_loop
    monitor_task = asyncio.create_task(
        credit_monitor_loop(run_id, org_id, cost_tier, pipeline, websocket)
    )

    voicemail_audio_accumulator = []
    voicemail_detection_done = False

    async def receive_loop():
        nonlocal voicemail_detection_done
        try:
            async for pcm_chunk in TelnyxTransport.receive_ulaw(websocket):
                await pipeline.push(audio_in(pcm_chunk))
                if call_type == "outbound" and not voicemail_detection_done:
                    voicemail_audio_accumulator.append(pcm_chunk)
                    total_bytes = sum(len(c) for c in voicemail_audio_accumulator)
                    # 5 seconds of 16kHz 16-bit PCM is 160000 bytes
                    if total_bytes >= 160000:
                        voicemail_detection_done = True
                        audio_data = b"".join(voicemail_audio_accumulator)
                        async def run_detection(data: bytes, r_id: int):
                            try:
                                from app.services.voicemail_detection import VoicemailDetector
                                res = await VoicemailDetector.detect(data)
                                is_vm = res.get("is_voicemail", False)
                                logger.info(f"Voicemail detection for run {r_id}: {is_vm}")
                                async with AsyncSessionLocal() as session:
                                    db_res = await session.execute(select(CallRun).where(CallRun.id == r_id))
                                    run_record = db_res.scalar_one_or_none()
                                    if run_record:
                                        run_record.voicemail = "true" if is_vm else "false"
                                        await session.commit()
                            except Exception as ex:
                                logger.error(f"Error during voicemail detection: {ex}")
                        asyncio.create_task(run_detection(audio_data, run_id))
        except Exception as e:
            logger.info(f"Telnyx receive loop ended/disconnected: {e}")

    async def send_loop():
        state = None
        try:
            while True:
                out_frame = await collecting_wrapper()
                if out_frame is None:
                    break
                if out_frame.type == FrameType.AUDIO_OUT:
                    _, state = await TelnyxTransport.send_pcm(websocket, out_frame.data, state)
                elif out_frame.type == FrameType.CALL_END:
                    break
        except Exception as e:
            logger.info(f"Telnyx send loop ended/disconnected: {e}")

    await pipeline.start()
    try:
        await asyncio.gather(receive_loop(), send_loop())
    finally:
        monitor_task.cancel()
        await pipeline.stop()
        from app.services.monitor_tracker import MonitorTracker
        MonitorTracker.end_call(run_id)
        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()

        # Check if voicemail detection wasn't triggered yet because call was too short
        if call_type == "outbound" and not voicemail_detection_done and voicemail_audio_accumulator:
            audio_data = b"".join(voicemail_audio_accumulator)
            try:
                from app.services.voicemail_detection import VoicemailDetector
                res = await VoicemailDetector.detect(audio_data)
                is_vm = res.get("is_voicemail", False)
                logger.info(f"Voicemail detection (fallback short-call) for run {run_id}: {is_vm}")
                async with AsyncSessionLocal() as db_session:
                    db_res = await db_session.execute(select(CallRun).where(CallRun.id == run_id))
                    run_record = db_res.scalar_one_or_none()
                    if run_record:
                        run_record.voicemail = "true" if is_vm else "false"
                        await db_session.commit()
            except Exception as ex:
                logger.error(f"Error during final voicemail detection: {ex}")

        # Update call run
        async with AsyncSessionLocal() as db_session:
            res = await db_session.execute(select(CallRun).where(CallRun.id == run_id))
            r = res.scalar_one_or_none()
            if r:
                r.status = "completed"
                r.ended_at = end_time
                r.duration_seconds = duration
                
                # Upload transcript to MinIO/local fallback
                transcript_text = "\n".join(transcript_segments)
                if transcript_text:
                    try:
                        filename = f"transcripts/{run_id}.txt"
                        from app.tasks.worker import upload_file_to_minio
                        from app.core.config import MINIO_BUCKET
                        path = upload_file_to_minio(MINIO_BUCKET, filename, transcript_text.encode("utf-8"), "text/plain")
                        r.transcript_path = path
                    except Exception as e:
                        logger.error(f"Failed to upload transcript to MinIO: {e}")
                
                await db_session.commit()

        from app.routes.calls import charge_final_credits
        await charge_final_credits(run_id, org_id, duration, agent.model_config)

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
                await arq_pool.close()
            
            asyncio.create_task(trigger_tasks())
        except Exception as e:
            logger.error(f"Failed to enqueue ARQ background tasks: {e}")


@router.post("/telephony/inbound/telnyx")
async def inbound_telnyx(
    call_control_id: str = Query(...),
    org_id: int = Query(...),
    agent_id: int = Query(...),
    from_number: str | None = Query(None, alias="from"),
    to_number: str | None = Query(None, alias="to"),
    call_type: str = Query("inbound"),
):
    from app.core.config import BACKEND_URL
    ws_base = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = f"{ws_base}/api/v1/telephony/ws/telnyx?call_control_id={quote(call_control_id)}&org_id={org_id}&agent_id={agent_id}&call_type={quote(call_type)}"
    if from_number:
        ws_url += f"&from={quote(from_number)}"
    if to_number:
        ws_url += f"&to={quote(to_number)}"
    
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Connect><WebSocket url={saxutils.quoteattr(ws_url)}/></Connect></Response>'
    return Response(content=twiml, media_type="application/xml")


@router.post("/telephony/inbound/twilio")
async def inbound_twilio(
    org_id: int = Query(...),
    agent_id: int = Query(...),
    From: str | None = Query(None),
    To: str | None = Query(None),
):
    from app.core.config import BACKEND_URL
    ws_base = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = f"{ws_base}/api/v1/telephony/ws/twilio?org_id={org_id}&agent_id={agent_id}"
    if From:
        ws_url += f"&from={quote(From)}"
    if To:
        ws_url += f"&to={quote(To)}"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url={saxutils.quoteattr(ws_url)} />
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.websocket("/telephony/ws/twilio")
async def twilio_ws(
    websocket: WebSocket,
    org_id: int = Query(..., description="Organization ID"),
    agent_id: int = Query(..., description="Agent ID"),
    from_number: str | None = Query(None, alias="from", description="Caller phone number"),
    to_number: str | None = Query(None, alias="to", description="Called phone number"),
    call_type: str = Query("inbound", description="Call type"),
    db: AsyncSession = Depends(get_db),
):
    await websocket.accept()
    # retrieve agent
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id)
    )
    agent = result.scalars().first()
    if not agent:
        await websocket.close(code=1008)
        return
    
    # check credits
    from app.models.organization import Organization
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = org_result.scalar_one_or_none()
    if not org or (org.balance_credits or 0.0) <= 0.0:
        await websocket.close(code=4002)
        return
    
    # context lookup
    from app.services.customer_memory import lookup_customer
    customer_context = await lookup_customer(db, org_id, from_number)

    run = CallRun(
        org_id=org_id,
        agent_id=agent.id,
        transport="twilio",
        call_type=call_type,
        status="running",
        caller_number=from_number,
        called_number=to_number,
        started_at=datetime.now(UTC),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    run_id = run.id

    from app.services.monitor_tracker import MonitorTracker
    MonitorTracker.register_call(
        run_id=run_id,
        agent_id=agent.id,
        agent_name=agent.name,
        transport="twilio",
        call_type=call_type,
        caller_number=from_number,
        called_number=to_number
    )

    has_visual_nodes = len(agent.graph.get("nodes", [])) > 0
    workflow_state = None
    if has_visual_nodes:
        from app.services.pipeline.workflow_engine import WorkflowState
        workflow_state = WorkflowState(agent.graph, context_variables=agent.context_variables)
        system_prompt, should_end = await workflow_state.execute_active_node()
        if should_end:
            await websocket.close(code=1000)
            return
    else:
        from app.routes.calls import _extract_system_prompt
        system_prompt = _extract_system_prompt(agent.graph)

    if customer_context:
        system_prompt += customer_context

    language = agent.model_config.get("language", "en")
    
    # build pipeline
    pipeline = build_pipeline(agent.model_config, system_prompt=system_prompt, language=language)

    # Find LLM processor and register tools
    llm_processor = None
    for p in pipeline.processors:
        if p.name in ("openai-llm", "groq-llm"):
            llm_processor = p
            break

    tools = []
    # Register search_knowledge_base if organization has documents
    async with AsyncSessionLocal() as session:
        from app.models.knowledge_base import KnowledgeBaseDocument
        doc_select = select(KnowledgeBaseDocument).where(
            KnowledgeBaseDocument.org_id == agent.org_id,
            (KnowledgeBaseDocument.agent_id == agent.id) | (KnowledgeBaseDocument.agent_id.is_(None))
        )
        doc_res = await session.execute(doc_select)
        has_docs = len(doc_res.scalars().all()) > 0

    if has_docs:
        tools.append({
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Search the knowledge base for documentation, guides, company policies to answer customer queries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search term or query containing relevant keywords."}
                    },
                    "required": ["query"]
                }
            }
        })

    if workflow_state:
        tools.append({
            "type": "function",
            "function": {
                "name": "submit_customer_answer",
                "description": "Submit a validated answer to the question asked, updating the context and transitioning call state.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string", "description": "The extracted value / answer from customer's speech."}
                    },
                    "required": ["value"]
                }
            }
        })
        tools.append({
            "type": "function",
            "function": {
                "name": "end_call",
                "description": "Terminate the call immediately.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        })

    if llm_processor and tools:
        llm_processor.set_tools(tools)

    transcript_segments = []

    async def collecting_wrapper():
        frame = await pipeline.collect()
        if frame:
            if frame.type == FrameType.STT_TRANSCRIPT:
                data = frame.data or {}
                if data.get("is_final"):
                    text = data.get("text", "").strip()
                    if text:
                        transcript_segments.append(f"User: {text}")
                        from app.services.monitor_tracker import MonitorTracker
                        MonitorTracker.update_transcript(run_id, text, "user")
            elif frame.type == FrameType.LLM_TEXT_COMPLETE:
                data = frame.data or {}
                text = data.get("text", "").strip()
                if text:
                    transcript_segments.append(f"Agent: {text}")
                    from app.services.monitor_tracker import MonitorTracker
                    MonitorTracker.update_transcript(run_id, text, "agent")
            elif frame.type == FrameType.TOOL_CALL:
                # Intercept tool calls, execute them, and push back TOOL_RESULT
                data = frame.data or {}
                name = data.get("name")
                args = data.get("arguments", {})
                call_id = data.get("call_id")
                result = None

                if name == "search_knowledge_base":
                    query = args.get("query", "")
                    async with AsyncSessionLocal() as session:
                        from app.services.rag_service import retrieve_context
                        result = await retrieve_context(session, agent.id, agent.org_id, query)
                elif name == "submit_customer_answer" and workflow_state:
                    val = args.get("value", "")
                    active_node = workflow_state.get_active_node()
                    if active_node and active_node.get("type") == "qa":
                        var_name = active_node.get("data", {}).get("expected_variable", "qa_ans")
                        workflow_state.context[var_name] = val
                    next_node = workflow_state.transition_to_next()
                    if next_node:
                        from app.services.pipeline.frame import Frame
                        new_prompt, should_end = await workflow_state.execute_active_node()
                        if should_end:
                            await pipeline.push(Frame(type=FrameType.CALL_END))
                            result = {"status": "call_ended"}
                        else:
                            if llm_processor:
                                llm_processor.system_prompt = new_prompt
                                llm_processor._messages.append({
                                    "role": "system",
                                    "content": f"[SYSTEM NOTICE: Workflow state changed. Active Prompt is now:\n{new_prompt}]"
                                })
                            result = {"status": "success", "next_node": next_node.get("id")}
                    else:
                        result = {"status": "success", "next_node": None}
                elif name == "end_call":
                    from app.services.pipeline.frame import Frame
                    await pipeline.push(Frame(type=FrameType.CALL_END))
                    result = {"status": "call_ended"}

                if result is not None:
                    from app.services.pipeline.frame import Frame
                    await pipeline.push(Frame(type=FrameType.TOOL_RESULT, data={"call_id": call_id, "result": result}))
        return frame
    start_time = datetime.now(UTC)

    cost_tier = agent.model_config.get("cost_tier", "standard")
    from app.routes.calls import credit_monitor_loop
    monitor_task = asyncio.create_task(
        credit_monitor_loop(run_id, org_id, cost_tier, pipeline, websocket)
    )

    voicemail_audio_accumulator = []
    voicemail_detection_done = False
    
    stream_sid = None
    
    # Twilio-specific receive loop
    async def receive_loop():
        nonlocal voicemail_detection_done, stream_sid
        from app.services.pipeline.transport.twilio_transport import TwilioTransport
        state = None
        try:
            async for message in websocket.iter_text():
                packet = json.loads(message)
                event = packet.get("event")
                
                if event == "start":
                    stream_sid = packet.get("start", {}).get("streamSid")
                    logger.info(f"Twilio Media Stream started: stream_sid={stream_sid}")
                elif event == "media":
                    payload_b64 = packet.get("media", {}).get("payload", "")
                    if payload_b64:
                        raw_ulaw = base64.b64decode(payload_b64)
                        pcm_8k = TwilioTransport.ulaw_to_pcm(raw_ulaw)
                        pcm_16k, state = TwilioTransport.resample(pcm_8k, TwilioTransport.INPUT_RATE, TwilioTransport.OUTPUT_RATE, state)
                        
                        await pipeline.push(audio_in(pcm_16k))
                        
                        # Voicemail accum
                        if call_type == "outbound" and not voicemail_detection_done:
                            voicemail_audio_accumulator.append(pcm_16k)
                            total_bytes = sum(len(c) for c in voicemail_audio_accumulator)
                            if total_bytes >= 160000:
                                voicemail_detection_done = True
                                audio_data = b"".join(voicemail_audio_accumulator)
                                async def run_detection(data: bytes, r_id: int):
                                    try:
                                        from app.services.voicemail_detection import VoicemailDetector
                                        res = await VoicemailDetector.detect(data)
                                        is_vm = res.get("is_voicemail", False)
                                        logger.info(f"Voicemail detection for run {r_id}: {is_vm}")
                                        async with AsyncSessionLocal() as session:
                                            db_res = await session.execute(select(CallRun).where(CallRun.id == r_id))
                                            run_record = db_res.scalar_one_or_none()
                                            if run_record:
                                                run_record.voicemail = "true" if is_vm else "false"
                                                await session.commit()
                                    except Exception as ex:
                                        logger.error(f"Error during voicemail detection: {ex}")
                                asyncio.create_task(run_detection(audio_data, run_id))
                elif event == "stop":
                    logger.info(f"Twilio Media Stream stopped: stream_sid={stream_sid}")
                    break
        except Exception as e:
            logger.info(f"Twilio receive loop disconnected: {e}")

    # Twilio-specific send loop
    async def send_loop():
        from app.services.pipeline.transport.twilio_transport import TwilioTransport
        state = None
        try:
            while True:
                out_frame = await collecting_wrapper()
                if out_frame is None:
                    break
                if out_frame.type == FrameType.AUDIO_OUT:
                    if stream_sid:
                        _, state = await TwilioTransport.send_pcm(websocket, stream_sid, out_frame.data, state)
                elif out_frame.type == FrameType.CALL_END:
                    break
        except Exception as e:
            logger.info(f"Twilio send loop disconnected: {e}")

    await pipeline.start()
    try:
        await asyncio.gather(receive_loop(), send_loop())
    finally:
        monitor_task.cancel()
        await pipeline.stop()
        from app.services.monitor_tracker import MonitorTracker
        MonitorTracker.end_call(run_id)
        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()

        if call_type == "outbound" and not voicemail_detection_done and voicemail_audio_accumulator:
            audio_data = b"".join(voicemail_audio_accumulator)
            try:
                from app.services.voicemail_detection import VoicemailDetector
                res = await VoicemailDetector.detect(audio_data)
                is_vm = res.get("is_voicemail", False)
                async with AsyncSessionLocal() as db_session:
                    db_res = await db_session.execute(select(CallRun).where(CallRun.id == run_id))
                    run_record = db_res.scalar_one_or_none()
                    if run_record:
                        run_record.voicemail = "true" if is_vm else "false"
                        await db_session.commit()
            except Exception as ex:
                logger.error(f"Error during final voicemail detection: {ex}")

        # update completed run record
        async with AsyncSessionLocal() as db_session:
            res = await db_session.execute(select(CallRun).where(CallRun.id == run_id))
            r = res.scalar_one_or_none()
            if r:
                r.status = "completed"
                r.ended_at = end_time
                r.duration_seconds = duration
                
                # Upload transcript
                transcript_text = "\n".join(transcript_segments)
                if transcript_text:
                    try:
                        filename = f"transcripts/{run_id}.txt"
                        from app.tasks.worker import upload_file_to_minio
                        from app.core.config import MINIO_BUCKET
                        path = upload_file_to_minio(MINIO_BUCKET, filename, transcript_text.encode("utf-8"), "text/plain")
                        r.transcript_path = path
                    except Exception as e:
                        logger.error(f"Failed to upload transcript to MinIO: {e}")
                
                await db_session.commit()

        from app.routes.calls import charge_final_credits
        await charge_final_credits(run_id, org_id, duration, agent.model_config)

        try:
            from arq import create_pool
            from arq.connections import RedisSettings
            from app.core.config import REDIS_URL
            redis_settings = RedisSettings.from_dsn(REDIS_URL)
            async def trigger_tasks():
                arq_pool = await create_pool(redis_settings)
                await arq_pool.enqueue_job("process_call_completion", run_id)
                await arq_pool.enqueue_job("update_customer_profile", run_id)
                await arq_pool.close()
            asyncio.create_task(trigger_tasks())
        except Exception as e:
            logger.error(f"Failed to enqueue ARQ background tasks: {e}")


