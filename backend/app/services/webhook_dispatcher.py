import httpx
import time
import hmac
import hashlib
import json
from sqlalchemy import select
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call_run import CallRun
from app.models.agent import Agent


async def dispatch_call_webhook(db: AsyncSession, run_id: int, event_type: str, payload_extra: dict = None) -> None:
    """
    Sends call lifecycle events (call.started, call.ended, call.transcript)
    to the agent's configured model_config["server_url"].
    Includes Retell AI-compatible event names and HMAC SHA256 signatures (X-Retell-Signature).
    """
    try:
        # Fetch run and agent
        result = await db.execute(
            select(CallRun, Agent)
            .join(Agent, CallRun.agent_id == Agent.id)
            .where(CallRun.id == run_id)
        )
        res = result.first()
        if not res:
            logger.warning(f"Webhook Dispatcher: CallRun {run_id} or bound Agent not found.")
            return
        run, agent = res

        server_url = agent.model_config.get("server_url") if agent.model_config else None
        if not server_url:
            logger.debug(f"Webhook Dispatcher: No server_url configured for Agent {agent.id}, skipping event {event_type}.")
            return

        # Map Auris event names to Retell event names
        retell_event_map = {
            "call.started": "call_started",
            "call.ended": "call_ended",
            "call.transcript": "call_analyzed",
            "call.analyzed": "call_analyzed",
        }
        retell_event_name = retell_event_map.get(event_type, event_type)

        # Construct the event payload (supporting both Auris and Retell formats)
        event_data = {
            "event": retell_event_name,
            "auris_event": event_type,
            "call": {
                "id": run.id,
                "agent_id": run.agent_id,
                "transport": run.transport,
                "call_type": run.call_type,
                "status": run.status,
                "caller_number": run.caller_number,
                "called_number": run.called_number,
                "disposition": run.disposition,
                "voicemail": (run.voicemail == "true") if isinstance(run.voicemail, str) else bool(run.voicemail),
                "created_at": run.created_at.isoformat() if run.created_at else None,
            },
            "data": {
                "call_id": str(run.id),
                "agent_id": str(run.agent_id),
                "call_status": run.status,
                "from_number": run.caller_number,
                "to_number": run.called_number,
                "direction": run.call_type or "inbound",
                "start_timestamp": int(run.started_at.timestamp() * 1000) if run.started_at else 0,
                "end_timestamp": int(run.ended_at.timestamp() * 1000) if run.ended_at else None,
                "duration_ms": int(run.duration_seconds * 1000) if run.duration_seconds else None,
                "transcript": run.summary or "",
            }
        }
        if payload_extra:
            event_data.update(payload_extra)
            if "data" in event_data and isinstance(payload_extra, dict):
                event_data["data"].update(payload_extra)

        # Generate Retell & Auris HMAC SHA256 Webhook Signatures
        timestamp = int(time.time() * 1000)
        secret = agent.model_config.get("webhook_secret") or agent.model_config.get("api_key") or "secret_key"
        body_str = json.dumps(event_data, separators=(",", ":"), ensure_ascii=False)
        digest = hmac.new(secret.encode("utf-8"), f"{body_str}{timestamp}".encode("utf-8"), hashlib.sha256).hexdigest()
        retell_signature = f"v={timestamp},d={digest}"

        headers = {
            "Content-Type": "application/json",
            "X-Auris-Event": event_type,
            "X-Retell-Event": retell_event_name,
            "X-Auris-Signature": retell_signature,
            "X-Retell-Signature": retell_signature,
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(server_url, content=body_str.encode("utf-8"), headers=headers)
            logger.info(f"Webhook {event_type} ({retell_event_name}) dispatched to {server_url}. Status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Failed to dispatch webhook event {event_type} for run {run_id}: {e}")
