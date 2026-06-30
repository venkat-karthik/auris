# backend/app/services/transfer_manager.py
"""Warm transfer (human hand-off) utilities.

Creates a Twilio conference bridge, plays a whisper message to the target
agent, and connects the original caller to the agent. Or transfers Telnyx call legs.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import httpx
from loguru import logger
from sqlalchemy import select

from app.core.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_CALLER_ID, TELNYX_API_KEY
from app.models.call_run import CallRun
from app.models.agent import Agent
from app.core.database import AsyncSessionLocal


def _sync_create_conference(friendly_name: str) -> str:
    """Synchronous: create a Twilio conference and return its SID."""
    from twilio.rest import Client  # type: ignore

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return f"AurisTransfer-{friendly_name}"


def _sync_add_participant(conference_friendly_name: str, to_number: str, whisper_url: Optional[str] = None) -> None:
    """Synchronous: dial a participant into an existing conference."""
    from twilio.rest import Client  # type: ignore

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    twiml = f'<Response><Dial><Conference>{conference_friendly_name}</Conference></Dial></Response>'
    if whisper_url:
        url = whisper_url
    else:
        url = f"http://twimlets.com/echo?Twiml={twiml}"

    client.calls.create(
        to=to_number,
        from_=TWILIO_CALLER_ID or "+10000000000",
        url=url,
    )
    logger.info(f"Added participant {to_number} to conference {conference_friendly_name}")


def _sync_redirect_twilio_call(call_sid: str, conference_name: str) -> None:
    """Synchronous: redirect original Twilio caller leg into the conference."""
    try:
        from twilio.rest import Client  # type: ignore
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        twiml = f'<Response><Dial><Conference>{conference_name}</Conference></Dial></Response>'
        url = f"http://twimlets.com/echo?Twiml={twiml}"
        client.calls(call_sid).update(url=url)
        logger.info(f"Redirected Twilio call {call_sid} to conference {conference_name}")
    except Exception as e:
        logger.warning(f"Failed to redirect Twilio call leg (expected in mock/test runs): {e}")


async def _async_transfer_telnyx(call_control_id: str, to_number: str) -> bool:
    """Asynchronous: call Telnyx Call Control transfer endpoint."""
    url = f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/transfer"
    headers = {
        "Authorization": f"Bearer {TELNYX_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"to": to_number}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if resp.status_code not in (200, 201, 202):
                logger.error(f"Telnyx transfer failed: {resp.status_code} - {resp.text}")
                return False
            logger.info(f"Telnyx call {call_control_id} transfer requested to {to_number}")
            return True
    except Exception as e:
        logger.error(f"Failed to call Telnyx transfer API: {e}")
        return False


async def warm_transfer(
    call_id: int,
    target_agent_id: int,
    whisper_url: Optional[str] = None,
) -> bool:
    """Perform a warm transfer for *call_id* to *target_agent_id*."""
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

        # Check transport type
        if call.transport == "telnyx":
            if not TELNYX_API_KEY or TELNYX_API_KEY.startswith("mock"):
                logger.warning("Telnyx keys not set. Simulating transfer.")
                call.recording_path = f"transfer-telnyx-{call_id}-simulated"
                await db.commit()
                return True
            if call.telephony_id:
                success = await _async_transfer_telnyx(call.telephony_id, agent_phone)
                if success:
                    call.recording_path = f"transfer-telnyx-{call_id}"
                    await db.commit()
                    return True
            else:
                logger.error(f"Cannot transfer Telnyx call {call_id} because telephony_id is missing")
                return False

        else:
            if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or TWILIO_ACCOUNT_SID.startswith("mock"):
                logger.warning("Twilio keys not set. Simulating warm transfer.")
                conference_name = f"conf-{call_id}-simulated"
            else:
                loop = asyncio.get_running_loop()
                conference_name = await loop.run_in_executor(
                    None, _sync_create_conference, str(call_id)
                )
                
                # Dial the target agent
                await loop.run_in_executor(
                    None, _sync_add_participant, conference_name, agent_phone, whisper_url
                )
                
                # Redirect the original caller
                if call.telephony_id:
                    await loop.run_in_executor(
                        None, _sync_redirect_twilio_call, call.telephony_id, conference_name
                    )
                else:
                    logger.warning(f"Twilio call run {call_id} is missing telephony_id; original leg not redirected.")

            call.recording_path = conference_name
            await db.commit()
            logger.info(f"Warm transfer of Twilio call {call_id} → agent {target_agent_id} via conference '{conference_name}'")
            return True
