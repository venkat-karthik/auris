import json
import logging
import secrets
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import BACKEND_URL
from app.core.database import AsyncSessionLocal
from app.dependencies.rate_limit import redis_client
from app.models.agent import Agent
from app.models.call_run import CallRun
from app.models.knowledge_base import KnowledgeBaseDocument
from app.services.pipeline.frame import Frame, FrameType

logger = logging.getLogger("auris.pipeline.tool_orchestrator")


class ToolOrchestrator:
    """Centralized orchestration of tool call interception, execution, and registration."""

    @staticmethod
    async def register_agent_tools(agent: Agent, workflow_state, llm_processor) -> list[dict]:
        """Build and register tool definitions for an agent based on org documents, workflow state, and custom config."""
        tools = []

        # Register search_knowledge_base if organization has documents
        async with AsyncSessionLocal() as session:
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

        # Register send_whatsapp_message tool
        tools.append({
            "type": "function",
            "function": {
                "name": "send_whatsapp_message",
                "description": "Send a WhatsApp text message containing an optional trackable link/URL to the customer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "The message body template (e.g. 'Click here to view your invoice: {link}')."},
                        "link_url": {"type": "string", "description": "The destination URL that the customer should visit (optional)."}
                    },
                    "required": ["message"]
                }
            }
        })

        # Register custom tools from agent configuration
        custom_tools = agent.model_config.get("tools", [])
        if custom_tools:
            tools.extend(custom_tools)

        if llm_processor:
            llm_processor.set_tools(tools)

        return tools

    @staticmethod
    async def handle_tool_call(
        frame: Frame,
        agent: Agent,
        run_id: int,
        pipeline,
        llm_processor=None,
        workflow_state=None,
        caller_number: str | None = None,
        transcript_segments: list[str] | None = None,
        db: AsyncSession | None = None,
    ) -> None:
        """Intercept a TOOL_CALL frame, execute the appropriate tool, and push the TOOL_RESULT frame back into the pipeline."""
        if frame.type != FrameType.TOOL_CALL:
            return

        data = frame.data or {}
        name = data.get("name")
        args = data.get("arguments", {})
        call_id = data.get("call_id")
        result = None

        if transcript_segments is None:
            transcript_segments = []

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
                if db is not None:
                    new_prompt, should_end = await workflow_state.execute_active_node(db=db, run_id=run_id)
                else:
                    async with AsyncSessionLocal() as session:
                        new_prompt, should_end = await workflow_state.execute_active_node(db=session, run_id=run_id)

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
                res = await session.execute(select(Agent).where(Agent.id == target_agent_id, Agent.org_id == agent.org_id))
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
            await pipeline.push(Frame(type=FrameType.CALL_END))
            result = {"status": "call_ended"}

        elif name == "send_whatsapp_message":
            msg_tmpl = args.get("message", "")
            link_url = args.get("link_url")
            sent_url = link_url
            if link_url:
                token = secrets.token_urlsafe(16)
                tracked_data = {
                    "call_run_id": run_id,
                    "original_url": link_url,
                    "clicked": False
                }
                await redis_client.set(f"tracked_link:{token}", json.dumps(tracked_data), ex=86400)
                sent_url = f"{BACKEND_URL}/api/v1/links/click/{token}"
                if "{link}" in msg_tmpl:
                    msg_text = msg_tmpl.replace("{link}", sent_url)
                else:
                    msg_text = f"{msg_tmpl} {sent_url}"
            else:
                msg_text = msg_tmpl

            from app.routes.whatsapp import send_whatsapp_message as raw_send_whatsapp
            target_number = caller_number or ""
            target_number = target_number.strip().replace(" ", "").replace("-", "")
            if target_number and not target_number.startswith("+"):
                target_number = "+" + target_number
            if target_number:
                success = await raw_send_whatsapp(target_number, msg_text)
                if success:
                    result = {"status": "sent", "recipient": target_number, "message_sent": msg_text}
                else:
                    result = {"status": "failed", "error": "WhatsApp sending API failed"}
            else:
                result = {"status": "failed", "error": "No valid caller phone number found to send to"}

        if result is None:
            # General-purpose server_url webhook for arbitrary tool calls
            server_url = agent.model_config.get("server_url")
            if server_url:
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
            await pipeline.push(Frame(type=FrameType.TOOL_RESULT, data={"call_id": call_id, "result": result}))
