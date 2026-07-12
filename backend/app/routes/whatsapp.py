from typing import List, Optional
from datetime import datetime, UTC, timezone, timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Query
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_org
from app.models.organization import Organization
from app.models.whatsapp_number import WhatsappNumber
from app.models.agent import Agent

logger = logging.getLogger("whatsapp")

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Numbers"])


class AddWhatsappNumberRequest(BaseModel):
    phone_number: str
    label: Optional[str] = None


class BindWhatsappNumberRequest(BaseModel):
    agent_id: Optional[int] = None


class WhatsappNumberResponse(BaseModel):
    id: int
    phone_number: str
    label: Optional[str]
    is_active: bool
    agent_id: Optional[int]
    agent_name: Optional[str]
    created_at: datetime


@router.get("", response_model=List[WhatsappNumberResponse])
async def list_whatsapp_numbers(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """List all WhatsApp numbers linked to the current organization."""
    query = select(WhatsappNumber).where(WhatsappNumber.org_id == org.id)
    result = await db.execute(query)
    numbers = result.scalars().all()

    response = []
    for num in numbers:
        agent_name = None
        if num.agent_id:
            agent_res = await db.execute(select(Agent.name).where(Agent.id == num.agent_id))
            agent_name = agent_res.scalar_one_or_none()

        response.append(WhatsappNumberResponse(
            id=num.id,
            phone_number=num.phone_number,
            label=num.label,
            is_active=num.is_active,
            agent_id=num.agent_id,
            agent_name=agent_name,
            created_at=num.created_at
        ))
    return response


@router.post("", response_model=WhatsappNumberResponse)
async def add_whatsapp_number(
    req: AddWhatsappNumberRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Link a WhatsApp Business number to the current organization."""
    # Check if number already exists
    existing = await db.execute(
        select(WhatsappNumber).where(WhatsappNumber.phone_number == req.phone_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This WhatsApp phone number is already registered in the platform."
        )

    num = WhatsappNumber(
        org_id=org.id,
        phone_number=req.phone_number,
        label=req.label or "WhatsApp Desk",
        is_active=True
    )
    db.add(num)
    await db.commit()
    await db.refresh(num)

    return WhatsappNumberResponse(
        id=num.id,
        phone_number=num.phone_number,
        label=num.label,
        is_active=num.is_active,
        agent_id=num.agent_id,
        agent_name=None,
        created_at=num.created_at
    )


@router.put("/{number_id}/bind", response_model=WhatsappNumberResponse)
async def bind_whatsapp_agent(
    number_id: int,
    req: BindWhatsappNumberRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Bind or unbind an agent handler to a WhatsApp number."""
    query = select(WhatsappNumber).where(WhatsappNumber.id == number_id, WhatsappNumber.org_id == org.id)
    result = await db.execute(query)
    num = result.scalar_one_or_none()
    if not num:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WhatsApp number not found.")

    agent_name = None
    if req.agent_id:
        agent_res = await db.execute(select(Agent).where(Agent.id == req.agent_id, Agent.org_id == org.id))
        agent = agent_res.scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
        num.agent_id = req.agent_id
        agent_name = agent.name
    else:
        num.agent_id = None

    await db.commit()
    await db.refresh(num)

    return WhatsappNumberResponse(
        id=num.id,
        phone_number=num.phone_number,
        label=num.label,
        is_active=num.is_active,
        agent_id=num.agent_id,
        agent_name=agent_name,
        created_at=num.created_at
    )


@router.delete("/{number_id}")
async def delete_whatsapp_number(
    number_id: int,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Disconnect a WhatsApp number from the workspace."""
    query = select(WhatsappNumber).where(WhatsappNumber.id == number_id, WhatsappNumber.org_id == org.id)
    result = await db.execute(query)
    num = result.scalar_one_or_none()
    if not num:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WhatsApp number not found.")

    await db.delete(num)
    await db.commit()
    return {"message": "WhatsApp number successfully disconnected."}


async def send_whatsapp_message(to_number: str, text: str) -> bool:
    from app.core.config import WHATSAPP_API_TOKEN, WHATSAPP_PHONE_NUMBER_ID
    if not WHATSAPP_API_TOKEN or WHATSAPP_API_TOKEN.startswith("mock") or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning(f"WhatsApp API keys not configured. Simulating outbound WhatsApp message to {to_number}: {text}")
        return True

    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {
            "body": text
        }
    }
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if resp.status_code in (200, 201):
                logger.info(f"Outbound WhatsApp message successfully sent to {to_number}")
                return True
            else:
                logger.error(f"WhatsApp API send failed with status {resp.status_code}: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to call WhatsApp send API: {e}")
        return False


@router.get("/webhook")
async def whatsapp_webhook_verification(
    mode: str = Query(..., alias="hub.mode"),
    challenge: str = Query(..., alias="hub.challenge"),
    verify_token: str = Query(..., alias="hub.verify_token"),
):
    """WhatsApp webhook verification endpoint."""
    from app.core.config import WHATSAPP_VERIFY_TOKEN
    if mode == "subscribe" and verify_token == WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Inbound webhook receiver for WhatsApp messages."""
    try:
        body = await request.json()
        logger.info(f"Received WhatsApp webhook event: {body}")

        # Extract message details
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                metadata = value.get("metadata", {})

                # Standardize recipient phone number from platform
                recipient_number = metadata.get("display_phone_number")
                if not recipient_number:
                    continue

                for msg in messages:
                    msg_type = msg.get("type")
                    if msg_type != "text":
                        continue

                    customer_number = msg.get("from")
                    message_text = msg.get("text", {}).get("body", "").strip()

                    if not customer_number or not message_text:
                        continue

                    # Standardize numbers
                    clean_recipient = recipient_number.strip().replace(" ", "").replace("-", "")
                    if not clean_recipient.startswith("+"):
                        clean_recipient = "+" + clean_recipient

                    clean_customer = customer_number.strip().replace(" ", "").replace("-", "")
                    if not clean_customer.startswith("+"):
                        clean_customer = "+" + clean_customer

                    # Find registered WhatsApp number and associated agent
                    num_res = await db.execute(
                        select(WhatsappNumber).where(
                            (WhatsappNumber.phone_number == clean_recipient) |
                            (WhatsappNumber.phone_number == recipient_number)
                        )
                    )
                    wa_number = num_res.scalar_one_or_none()
                    if not wa_number or not wa_number.agent_id:
                        logger.warning(f"WhatsApp number {recipient_number} not registered or not bound to agent.")
                        continue

                    # Load Agent
                    agent_res = await db.execute(
                        select(Agent).where(Agent.id == wa_number.agent_id)
                    )
                    agent = agent_res.scalar_one_or_none()
                    if not agent:
                        logger.error(f"Agent {wa_number.agent_id} not found.")
                        continue

                    # Find or create a running CallRun of transport='text'
                    from app.models.call_run import CallRun
                    run_res = await db.execute(
                        select(CallRun).where(
                            CallRun.org_id == wa_number.org_id,
                            CallRun.agent_id == agent.id,
                            CallRun.transport == "text",
                            CallRun.caller_number == clean_customer,
                            CallRun.status == "running"
                        ).order_by(CallRun.created_at.desc())
                    )
                    run = run_res.scalar_one_or_none()

                    if not run:
                        run = CallRun(
                            org_id=wa_number.org_id,
                            agent_id=agent.id,
                            transport="text",
                            call_type="inbound",
                            status="running",
                            caller_number=clean_customer,
                            called_number=clean_recipient,
                            started_at=datetime.now(UTC),
                            initial_context={}
                        )
                        db.add(run)
                        await db.flush()

                    # Load message history
                    ctx = dict(run.gathered_context or {})
                    history = ctx.get("whatsapp_messages", [])
                    history.append({"role": "user", "content": message_text})

                    # Build prompt
                    from app.routes.calls import _extract_system_prompt
                    system_prompt = _extract_system_prompt(agent.graph)

                    # Lookup customer memory
                    from app.services.customer_memory import lookup_customer
                    customer_context = await lookup_customer(db, wa_number.org_id, clean_customer)
                    if customer_context:
                        system_prompt += "\n" + customer_context

                    # LLM Generation
                    from app.core.config import OPENAI_API_KEY
                    import httpx

                    llm_messages = [{"role": "system", "content": system_prompt}] + history
                    reply_text = "Hello! This is a mock reply from Auris WhatsApp agent."

                    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("mock"):
                        try:
                            llm_model = agent.model_config.get("llm", {}).get("model", "gpt-4o-mini")
                            async with httpx.AsyncClient() as client:
                                resp = await client.post(
                                    "https://api.openai.com/v1/chat/completions",
                                    headers={
                                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                                        "Content-Type": "application/json"
                                    },
                                    json={
                                        "model": llm_model,
                                        "messages": llm_messages,
                                        "temperature": 0.7,
                                        "max_tokens": 300
                                    },
                                    timeout=15.0
                                )
                                if resp.status_code == 200:
                                    reply_text = resp.json()["choices"][0]["message"]["content"]
                                else:
                                    logger.error(f"WhatsApp LLM completion failed: {resp.status_code} - {resp.text}")
                        except Exception as e:
                            logger.error(f"Failed to generate LLM reply: {e}")

                    history.append({"role": "assistant", "content": reply_text})
                    ctx["whatsapp_messages"] = history
                    run.gathered_context = ctx
                    await db.commit()

                    # Send response back to customer
                    await send_whatsapp_message(clean_customer, reply_text)

    except Exception as e:
        logger.error(f"Error handling WhatsApp webhook: {e}")

    return {"status": "event_received"}


class SendMessageRequest(BaseModel):
    to_number: str
    message: str


class WhatsappTemplateResponse(BaseModel):
    name: str
    language: str
    status: str
    components: list[dict] = []


class SendFollowupRequest(BaseModel):
    call_run_id: int
    template_name: str


@router.get("/templates", response_model=list[WhatsappTemplateResponse])
async def list_whatsapp_templates(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """List available WhatsApp message templates."""
    return [
        WhatsappTemplateResponse(
            name="post_call_summary_v1",
            language="en_US",
            status="APPROVED",
            components=[{"type": "BODY", "text": "Hi {{1}}, thanks for speaking with {{2}} today. Summary: {{3}}"}]
        ),
        WhatsappTemplateResponse(
            name="voicemail_followup",
            language="en_US",
            status="APPROVED",
            components=[{"type": "BODY", "text": "We missed you! Our AI agent tried calling regarding {{1}}. Reply here anytime."}]
        )
    ]


@router.post("/send")
async def send_whatsapp_followup(
    req: SendFollowupRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Send template follow-up message linked to a call run."""
    from app.models.call_run import CallRun
    run_res = await db.execute(select(CallRun).where(CallRun.id == req.call_run_id, CallRun.org_id == org.id))
    run = run_res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Call run not found")

    to_num = (run.customer_number or "").strip()
    if not to_num:
        raise HTTPException(status_code=400, detail="No customer number attached to this call run")

    success = await send_whatsapp_message(to_num, f"Template {req.template_name} sent regarding call #{req.call_run_id}")
    return {"message": "Follow-up message sent successfully", "success": success}


@router.post("/{number_id}/send")
async def send_whatsapp_message_route(
    number_id: int,
    req: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Send an outbound WhatsApp message and log it in the conversation history."""
    query = select(WhatsappNumber).where(WhatsappNumber.id == number_id, WhatsappNumber.org_id == org.id)
    result = await db.execute(query)
    num = result.scalar_one_or_none()
    if not num:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WhatsApp number not found.")

    to_num = req.to_number.strip().replace(" ", "").replace("-", "")
    if not to_num.startswith("+"):
        to_num = "+" + to_num

    # Find or create a running CallRun of transport='text'
    from app.models.call_run import CallRun
    run_res = await db.execute(
        select(CallRun).where(
            CallRun.org_id == org.id,
            CallRun.agent_id == num.agent_id,
            CallRun.transport == "text",
            CallRun.caller_number == to_num,
            CallRun.status == "running"
        ).order_by(CallRun.created_at.desc())
    )
    run = run_res.scalar_one_or_none()
    if not run and num.agent_id:
        run = CallRun(
            org_id=org.id,
            agent_id=num.agent_id,
            transport="text",
            call_type="outbound",
            status="running",
            caller_number=to_num,
            called_number=num.phone_number,
            started_at=datetime.now(UTC),
            initial_context={}
        )
        db.add(run)
        await db.flush()

    if run:
        ctx = dict(run.gathered_context or {})
        history = ctx.get("whatsapp_messages", [])
        history.append({"role": "assistant", "content": req.message})
        ctx["whatsapp_messages"] = history
        run.gathered_context = ctx
        await db.commit()

    success = await send_whatsapp_message(to_num, req.message)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send WhatsApp message.")

    return {"message": "WhatsApp message sent successfully."}
