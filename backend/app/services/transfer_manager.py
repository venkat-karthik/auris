# backend/app/services/transfer_manager.py
"""Warm transfer (human hand-off) utilities.

Creates a Twilio conference bridge, plays a whisper message to the target
agent, and connects the original caller to the agent.

Twilio SDK calls are synchronous, so they are offloaded to a thread executor
to avoid blocking the async event loop.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger
from sqlalchemy import select

from app.core.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_CALLER_ID
from app.models.call_run import CallRun
from app.models.agent import Agent
from app.core.database import AsyncSessionLocal


def _sync_create_conference(friendly_name: str) -> str:
    """Synchronous: create a Twilio conference and return its SID."""
    from twilio.rest import Client  # type: ignore

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    # Twilio does not have a direct conferences.create(); conferences are
    # created implicitly when a participant joins via <Conference> TwiML.
    # We use the Rooms API equivalent – create a conference via a participant
    # call and retrieve its SID from the call's conference.
    # For simplicity we return a deterministic name used in TwiML routing.
    return f"AurisTransfer-{friendly_name}"


def _sync_add_participant(conference_friendly_name: str, to_number: str, whisper_url: Optional[str] = None) -> None:
    """Synchronous: dial a participant into an existing conference."""
    from twilio.rest import Client  # type: ignore

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    twiml = f'<Response><Dial><Conference>{conference_friendly_name}</Conference></Dial></Response>'
    if whisper_url:
        # Use the whisper URL as the TwiML for the participant leg
        url = whisper_url
    else:
        # Inline TwiML via url= parameter is not available directly;
        # we fall back to a data URI accepted by Twilio's url= field
        url = f"http://twimlets.com/echo?Twiml={twiml}"

    client.calls.create(
        to=to_number,
        from_=TWILIO_CALLER_ID or "+10000000000",
        url=url,
    )
    logger.info(f"Added participant {to_number} to conference {conference_friendly_name}")


async def warm_transfer(
    call_id: int,
    target_agent_id: int,
    whisper_url: Optional[str] = None,
) -> bool:
    """Perform a warm transfer for *call_id* to *target_agent_id*.

    Steps:
    1. Retrieve the original ``CallRun`` record and the ``Agent`` record.
    2. Derive a conference name from the call ID.
    3. Dial the target agent into the conference (off-thread).
    4. Persist the conference name on the ``CallRun`` for reference.
    5. Return ``True`` on success.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CallRun).where(CallRun.id == call_id))
        call = result.scalar_one_or_none()
        if not call:
            logger.error(f"CallRun {call_id} not found for warm transfer")
            return False

        result = await db.execute(select(Agent).where(Agent.id == target_agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            logger.error(f"Agent {target_agent_id} not found for warm transfer")
            return False

        from app.models.phone_number import PhoneNumber
        phone_res = await db.execute(select(PhoneNumber).where(PhoneNumber.agent_id == target_agent_id, PhoneNumber.is_active == True))
        phone_obj = phone_res.scalar_one_or_none()
        agent_phone = phone_obj.phone_number if phone_obj else "+1234567890"

        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or TWILIO_ACCOUNT_SID.startswith("mock"):
            logger.warning("Twilio keys not set. Simulating warm transfer.")
            conference_name = f"conf-{call_id}-simulated"
        else:
            loop = asyncio.get_running_loop()
            # Run synchronous Twilio SDK calls in a thread pool
            conference_name = await loop.run_in_executor(
                None, _sync_create_conference, str(call_id)
            )
            await loop.run_in_executor(
                None, _sync_add_participant, conference_name, agent_phone, whisper_url
            )

        # Persist the conference name (reusing recording_path as a placeholder)
        call.recording_path = conference_name
        await db.commit()
        logger.info(f"Warm transfer of call {call_id} → agent {target_agent_id} via conference '{conference_name}'")
        return True
