import httpx
from sqlalchemy import select
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call_run import CallRun
from app.models.agent import Agent


async def dispatch_call_webhook(db: AsyncSession, run_id: int, event_type: str, payload_extra: dict = None) -> None:
    """
    Sends call lifecycle events (call.started, call.ended, call.transcript)
    to the agent's configured model_config["server_url"].
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

        # Construct the event payload
        event_data = {
            "event": event_type,
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
            }
        }
        if payload_extra:
            event_data.update(payload_extra)

        headers = {
            "Content-Type": "application/json",
            "X-Auris-Event": event_type
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(server_url, json=event_data, headers=headers)
            logger.info(f"Webhook {event_type} dispatched to {server_url}. Status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Failed to dispatch webhook event {event_type} for run {run_id}: {e}")
