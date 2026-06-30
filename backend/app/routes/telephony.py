from fastapi import APIRouter, WebSocket, Query, HTTPException, Depends, Response, Request
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
from app.services.pipeline.frame import audio_in, FrameType, Frame
from app.models.agent import Agent
from app.models.call_run import CallRun
from app.core.database import get_db, AsyncSessionLocal
from app.core.config import TELNYX_PUBLIC_KEY, TWILIO_AUTH_TOKEN

async def verify_telnyx_signature(request: Request, public_key_str: str) -> bool:
    signature = request.headers.get("telnyx-signature-ed25519")
    timestamp = request.headers.get("telnyx-timestamp")
    if not signature or not timestamp:
        return False
    try:
        body_bytes = await request.body()
        from cryptography.hazmat.primitives.asymmetric import ed25519
        try:
            pub_bytes = bytes.fromhex(public_key_str)
        except ValueError:
            pub_bytes = base64.b64decode(public_key_str)
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        
        try:
            sig_bytes = base64.b64decode(signature)
        except ValueError:
            sig_bytes = bytes.fromhex(signature)
            
        message = timestamp.encode('utf-8') + body_bytes
        pub_key.verify(sig_bytes, message)
        return True
    except Exception as e:
        logger.error(f"Telnyx signature validation failed: {e}")
        return False

async def verify_twilio_signature(request: Request, auth_token: str) -> bool:
    signature = request.headers.get("x-twilio-signature")
    if not signature:
        return False
    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(auth_token)
        url = str(request.url)
        form_data = await request.form()
        params = dict(form_data)
        return validator.validate(url, params, signature)
    except Exception as e:
        logger.error(f"Twilio signature validation failed: {e}")
        return False

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
    campaign_id: int | None = Query(None, description="Campaign ID"),
    contact_id: int | None = Query(None, description="Contact ID"),
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
        telephony_id=call_control_id,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    run_id = run.id
    from app.services.webhook_dispatcher import dispatch_call_webhook
    asyncio.create_task(dispatch_call_webhook(db, run_id, "call.started"))

    # Associate CampaignContact to CallRun immediately
    if contact_id:
        from app.models.campaign import CampaignContact
        contact_res = await db.execute(
            select(CampaignContact).where(CampaignContact.id == contact_id)
        )
        contact = contact_res.scalar_one_or_none()
        if contact:
            contact.call_run_id = run_id
            await db.commit()


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
        system_prompt, should_end = await workflow_state.execute_active_node(db=db, run_id=run_id)
        if should_end:
            await websocket.close(code=1000)
            return
    else:
        from app.routes.calls import _extract_system_prompt
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
    
    # Build pipeline based on agent config
    pipeline = build_pipeline(agent.model_config, system_prompt=system_prompt, language=language)

    # Find LLM processor and register tools
    llm_processor = None
    for p in pipeline.processors:
        if p.name in ("openai-llm", "groq-llm", "anthropic-llm"):
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

    # Register transfer_to_agent tool
    tools.append({
        "type": "function",
        "function": {
            "name": "transfer_to_agent",
            "description": "Transfer the call to another specialized virtual agent (e.g. support, billing, sales).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_agent_id": {"type": "integer", "description": "The ID of the target agent to transfer to."}
                },
                "required": ["target_agent_id"]
            }
        }
    })

    # Register custom tools from agent configuration
    custom_tools = agent.model_config.get("tools", [])
    if custom_tools:
        tools.extend(custom_tools)

    if llm_processor:
        llm_processor.set_tools(tools)

    
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
                        new_prompt, should_end = await workflow_state.execute_active_node(db=db, run_id=run_id)
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
                elif name == "transfer_to_agent":
                    target_agent_id = args.get("target_agent_id")
                    async with AsyncSessionLocal() as session:
                        res = await session.execute(select(Agent).where(Agent.id == target_agent_id, Agent.org_id == org_id))
                        target_agent = res.scalar_one_or_none()
                        if target_agent:
                            cr_res = await session.execute(select(CallRun).where(CallRun.id == run_id))
                            cr_rec = cr_res.scalar_one_or_none()
                            if cr_rec:
                                cr_rec.agent_id = target_agent.id
                                await session.commit()
                            
                            from app.routes.calls import _extract_system_prompt
                            new_prompt = _extract_system_prompt(target_agent.graph)
                            if llm_processor:
                                llm_processor.system_prompt = new_prompt
                                llm_processor._messages.append({
                                    "role": "system",
                                    "content": f"[SYSTEM NOTICE: Call transferred to {target_agent.name}. System prompt updated to:\n{new_prompt}]"
                                })
                            result = {"status": "success", "message": f"Transferred to agent {target_agent.name}"}
                        else:
                            result = {"status": "failed", "error": "Agent not found"}
                elif name == "end_call":
                    from app.services.pipeline.frame import Frame
                    await pipeline.push(Frame(type=FrameType.CALL_END))
                    result = {"status": "call_ended"}

                if result is None:
                    # General-purpose server_url webhook for arbitrary tool calls
                    server_url = agent.model_config.get("server_url")
                    if server_url:
                        import httpx
                        transcript_so_far = "\n".join(transcript_segments)
                        try:
                            async with httpx.AsyncClient() as client:
                                payload = {
                                    "tool_name": name,
                                    "arguments": args,
                                    "call_id": run_id,
                                    "transcript_so_far": transcript_so_far
                                }
                                resp = await client.post(server_url, json=payload, timeout=5.0)
                                if resp.status_code >= 200 and resp.status_code < 300:
                                    result = resp.json()
                                else:
                                    result = {"error": f"Server returned status {resp.status_code}"}
                        except Exception as e:
                            logger.error(f"Failed to call server_url tool {name}: {e}")
                            result = {"error": str(e)}

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
    # Push CALL_START to start the pipeline conversation
    await pipeline.push(Frame(type=FrameType.CALL_START, data={"run_id": run_id}))
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
                        r.recording_path = rec_path
                    except Exception as e:
                        logger.error(f"Failed to upload recording to MinIO: {e}")
                
                # Save usage stats
                r.usage_stats = usage_stats
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
                await arq_pool.enqueue_job("run_post_call_analysis", run_id)
                if contact_id:
                    await arq_pool.enqueue_job("update_campaign_contact_status", run_id, contact_id)
                await arq_pool.close()
            
            asyncio.create_task(trigger_tasks())
        except Exception as e:
            logger.error(f"Failed to enqueue ARQ background tasks: {e}")



@router.post("/telephony/inbound/telnyx")
async def inbound_telnyx(
    request: Request,
    call_control_id: str = Query(...),
    org_id: int | None = Query(None),
    agent_id: int | None = Query(None),
    from_number: str | None = Query(None, alias="from"),
    to_number: str | None = Query(None, alias="to"),
    call_type: str = Query("inbound"),
    campaign_id: int | None = Query(None),
    contact_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # Verify Telnyx Webhook Signature
    if TELNYX_PUBLIC_KEY and not TELNYX_PUBLIC_KEY.startswith("mock"):
        if not await verify_telnyx_signature(request, TELNYX_PUBLIC_KEY):
            raise HTTPException(status_code=403, detail="Invalid Telnyx signature")

    # Check if request is JSON (Call Control Event Callback)
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            event_type = body.get("data", {}).get("event_type")
            if event_type in ("call.hangup", "call.failed", "call.no-answer") and contact_id:
                from app.models.campaign import CampaignContact
                async with AsyncSessionLocal() as session:
                    res = await session.execute(select(CampaignContact).where(CampaignContact.id == contact_id))
                    contact = res.scalar_one_or_none()
                    if contact and contact.status == "in_progress" and contact.call_run_id is None:
                        if contact.attempts < 3:
                            contact.status = "pending"
                        else:
                            contact.status = "failed"
                        await session.commit()
                        logger.info(f"Telnyx callback: campaign contact {contact_id} marked as {contact.status} (never answered)")
            return Response(content="Event processed", media_type="text/plain")
        except Exception as e:
            logger.error(f"Error processing Telnyx Call Control callback: {e}")
            return Response(content="Error", media_type="text/plain")

    if (org_id is None or agent_id is None) and to_number:
        from app.models.phone_number import PhoneNumber
        clean_num = to_number
        if not clean_num.startswith("+") and len(clean_num) > 8:
            clean_num = "+" + clean_num
        
        num_query = select(PhoneNumber).where(
            (PhoneNumber.phone_number == to_number) | 
            (PhoneNumber.phone_number == clean_num)
        )
        res = await db.execute(num_query)
        db_num = res.scalar_one_or_none()
        if db_num:
            org_id = db_num.org_id
            agent_id = db_num.agent_id
            logger.info(f"Dynamically routed inbound Telnyx call on {to_number} to org {org_id}, agent {agent_id}")
        else:
            logger.warning(f"Inbound Telnyx call to unmapped number {to_number}")

    if org_id is None or agent_id is None:
        raise HTTPException(status_code=404, detail="Phone number mapping not found or incomplete")

    from app.core.config import BACKEND_URL
    ws_base = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = f"{ws_base}/api/v1/telephony/ws/telnyx?call_control_id={quote(call_control_id)}&org_id={org_id}&agent_id={agent_id}&call_type={quote(call_type)}"
    if from_number:
        ws_url += f"&from={quote(from_number)}"
    if to_number:
        ws_url += f"&to={quote(to_number)}"
    if campaign_id:
        ws_url += f"&campaign_id={campaign_id}"
    if contact_id:
        ws_url += f"&contact_id={contact_id}"
    
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Connect><WebSocket url={saxutils.quoteattr(ws_url)}/></Connect></Response>'
    return Response(content=twiml, media_type="application/xml")


@router.post("/telephony/inbound/twilio")
async def inbound_twilio(
    request: Request,
    org_id: int | None = Query(None),
    agent_id: int | None = Query(None),
    From: str | None = Query(None),
    To: str | None = Query(None),
    campaign_id: int | None = Query(None),
    contact_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # Verify Twilio Webhook Signature
    if TWILIO_AUTH_TOKEN and not TWILIO_AUTH_TOKEN.startswith("mock"):
        if not await verify_twilio_signature(request, TWILIO_AUTH_TOKEN):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    if (org_id is None or agent_id is None) and To:
        from app.models.phone_number import PhoneNumber
        clean_num = To
        if not clean_num.startswith("+") and len(clean_num) > 8:
            clean_num = "+" + clean_num

        num_query = select(PhoneNumber).where(
            (PhoneNumber.phone_number == To) | 
            (PhoneNumber.phone_number == clean_num)
        )
        res = await db.execute(num_query)
        db_num = res.scalar_one_or_none()
        if db_num:
            org_id = db_num.org_id
            agent_id = db_num.agent_id
            logger.info(f"Dynamically routed inbound Twilio call on {To} to org {org_id}, agent {agent_id}")
        else:
            logger.warning(f"Inbound Twilio call to unmapped number {To}")

    if org_id is None or agent_id is None:
        raise HTTPException(status_code=404, detail="Phone number mapping not found or incomplete")

    from app.core.config import BACKEND_URL
    ws_base = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = f"{ws_base}/api/v1/telephony/ws/twilio?org_id={org_id}&agent_id={agent_id}"
    if From:
        ws_url += f"&from={quote(From)}"
    if To:
        ws_url += f"&to={quote(To)}"
    if campaign_id:
        ws_url += f"&campaign_id={campaign_id}"
    if contact_id:
        ws_url += f"&contact_id={contact_id}"

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
    campaign_id: int | None = Query(None, description="Campaign ID"),
    contact_id: int | None = Query(None, description="Contact ID"),
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
    from app.services.webhook_dispatcher import dispatch_call_webhook
    asyncio.create_task(dispatch_call_webhook(db, run_id, "call.started"))

    # Associate CampaignContact to CallRun immediately
    if contact_id:
        from app.models.campaign import CampaignContact
        contact_res = await db.execute(
            select(CampaignContact).where(CampaignContact.id == contact_id)
        )
        contact = contact_res.scalar_one_or_none()
        if contact:
            contact.call_run_id = run_id
            await db.commit()


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
        system_prompt, should_end = await workflow_state.execute_active_node(db=db, run_id=run_id)
        if should_end:
            await websocket.close(code=1000)
            return
    else:
        from app.routes.calls import _extract_system_prompt
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
    
    # build pipeline
    pipeline = build_pipeline(agent.model_config, system_prompt=system_prompt, language=language)

    # Find LLM processor and register tools
    llm_processor = None
    for p in pipeline.processors:
        if p.name in ("openai-llm", "groq-llm", "anthropic-llm"):
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

    # Register transfer_to_agent tool
    tools.append({
        "type": "function",
        "function": {
            "name": "transfer_to_agent",
            "description": "Transfer the call to another specialized virtual agent (e.g. support, billing, sales).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_agent_id": {"type": "integer", "description": "The ID of the target agent to transfer to."}
                },
                "required": ["target_agent_id"]
            }
        }
    })

    # Register custom tools from agent configuration
    custom_tools = agent.model_config.get("tools", [])
    if custom_tools:
        tools.extend(custom_tools)

    if llm_processor:
        llm_processor.set_tools(tools)

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
                        new_prompt, should_end = await workflow_state.execute_active_node(db=db, run_id=run_id)
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
                elif name == "transfer_to_agent":
                    target_agent_id = args.get("target_agent_id")
                    async with AsyncSessionLocal() as session:
                        res = await session.execute(select(Agent).where(Agent.id == target_agent_id, Agent.org_id == org_id))
                        target_agent = res.scalar_one_or_none()
                        if target_agent:
                            cr_res = await session.execute(select(CallRun).where(CallRun.id == run_id))
                            cr_rec = cr_res.scalar_one_or_none()
                            if cr_rec:
                                cr_rec.agent_id = target_agent.id
                                await session.commit()
                            
                            from app.routes.calls import _extract_system_prompt
                            new_prompt = _extract_system_prompt(target_agent.graph)
                            if llm_processor:
                                llm_processor.system_prompt = new_prompt
                                llm_processor._messages.append({
                                    "role": "system",
                                    "content": f"[SYSTEM NOTICE: Call transferred to {target_agent.name}. System prompt updated to:\n{new_prompt}]"
                                })
                            result = {"status": "success", "message": f"Transferred to agent {target_agent.name}"}
                        else:
                            result = {"status": "failed", "error": "Agent not found"}
                elif name == "end_call":
                    from app.services.pipeline.frame import Frame
                    await pipeline.push(Frame(type=FrameType.CALL_END))
                    result = {"status": "call_ended"}

                if result is None:
                    # General-purpose server_url webhook for arbitrary tool calls
                    server_url = agent.model_config.get("server_url")
                    if server_url:
                        import httpx
                        transcript_so_far = "\n".join(transcript_segments)
                        try:
                            async with httpx.AsyncClient() as client:
                                payload = {
                                    "tool_name": name,
                                    "arguments": args,
                                    "call_id": run_id,
                                    "transcript_so_far": transcript_so_far
                                }
                                resp = await client.post(server_url, json=payload, timeout=5.0)
                                if resp.status_code >= 200 and resp.status_code < 300:
                                    result = resp.json()
                                else:
                                    result = {"error": f"Server returned status {resp.status_code}"}
                        except Exception as e:
                            logger.error(f"Failed to call server_url tool {name}: {e}")
                            result = {"error": str(e)}

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
                    call_sid = packet.get("start", {}).get("callSid")
                    logger.info(f"Twilio Media Stream started: stream_sid={stream_sid}, call_sid={call_sid}")
                    if call_sid:
                        async with AsyncSessionLocal() as session:
                            res = await session.execute(select(CallRun).where(CallRun.id == run_id))
                            r_rec = res.scalar_one_or_none()
                            if r_rec:
                                r_rec.telephony_id = call_sid
                                await session.commit()
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
    # Push CALL_START to start the pipeline conversation
    await pipeline.push(Frame(type=FrameType.CALL_START, data={"run_id": run_id, "call_type": call_type}))
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
                        r.recording_path = rec_path
                    except Exception as e:
                        logger.error(f"Failed to upload recording to MinIO: {e}")
                
                # Save usage stats
                r.usage_stats = usage_stats
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
                await arq_pool.enqueue_job("run_post_call_analysis", run_id)
                if contact_id:
                    await arq_pool.enqueue_job("update_campaign_contact_status", run_id, contact_id)
                await arq_pool.close()
            asyncio.create_task(trigger_tasks())
        except Exception as e:
            logger.error(f"Failed to enqueue ARQ background tasks: {e}")
