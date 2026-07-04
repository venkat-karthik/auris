"""
Auris - Retell REST API Compatibility Router
Implements exact Retell AI endpoints and schemas so official Retell SDKs (Python & TypeScript)
can connect to Auris with zero code changes by simply setting `base_url`.
"""
from datetime import UTC, datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_org, get_current_user
from sqlalchemy.orm.attributes import flag_modified
from app.models.agent import Agent
from app.models.call_run import CallRun
from app.models.phone_number import PhoneNumber
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(tags=["retell-compat"])


# ── Retell Schemas ───────────────────────────────────────────────────────────

class RetellResponseEngine(BaseModel):
    type: str = "retell-llm"
    llm_id: Optional[str] = None
    url: Optional[str] = None


class RetellAgentCreateRequest(BaseModel):
    agent_name: Optional[str] = "Auris Retell Agent"
    response_engine: Optional[dict[str, Any]] = None
    voice_id: Optional[str] = "11labs-Adrian"
    language: Optional[str] = "en-US"
    webhook_url: Optional[str] = None
    fallback_voice_ids: Optional[list[str]] = None
    ambient_sound: Optional[str] = None
    enable_backchannel: Optional[bool] = True


class RetellAgentUpdateRequest(BaseModel):
    agent_name: Optional[str] = None
    response_engine: Optional[dict[str, Any]] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None
    webhook_url: Optional[str] = None
    fallback_voice_ids: Optional[list[str]] = None
    ambient_sound: Optional[str] = None
    enable_backchannel: Optional[bool] = None


class RetellAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    response_engine: dict[str, Any]
    voice_id: str
    language: str
    webhook_url: Optional[str] = None
    last_modification_timestamp: int


class RetellWebCallRequest(BaseModel):
    agent_id: str
    metadata: Optional[dict[str, Any]] = None
    retell_llm_dynamic_variables: Optional[dict[str, Any]] = None


class RetellWebCallResponse(BaseModel):
    access_token: str
    call_id: str


class RetellPhoneCallRequest(BaseModel):
    from_number: str
    to_number: str
    agent_id: str
    metadata: Optional[dict[str, Any]] = None
    retell_llm_dynamic_variables: Optional[dict[str, Any]] = None


class RetellCallResponse(BaseModel):
    call_id: str
    agent_id: str
    call_status: str
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    direction: str = "inbound"
    start_timestamp: int
    end_timestamp: Optional[int] = None
    duration_ms: Optional[int] = None
    transcript: Optional[str] = ""
    recording_url: Optional[str] = None


class RetellPhoneNumberRequest(BaseModel):
    phone_number: Optional[str] = None
    area_code: Optional[int] = None
    agent_id: Optional[str] = None


class RetellPhoneNumberResponse(BaseModel):
    phone_number: str
    phone_number_pretty: str
    agent_id: Optional[str] = None
    area_code: int
    last_modification_timestamp: int


# ── Helper Functions ─────────────────────────────────────────────────────────

def _format_agent(agent: Agent) -> RetellAgentResponse:
    cfg = agent.model_config or {}
    resp_engine = cfg.get("response_engine", {"type": "retell-llm"})
    if cfg.get("llm", {}).get("provider") in ("retell-custom-llm", "custom-websocket"):
        resp_engine = {
            "type": "custom-llm",
            "url": cfg.get("custom_llm_websocket_url", "")
        }
    
    ts = int(agent.updated_at.timestamp() * 1000) if agent.updated_at else int(datetime.now(UTC).timestamp() * 1000)
    return RetellAgentResponse(
        agent_id=str(agent.id),
        agent_name=agent.name or "Auris Agent",
        response_engine=resp_engine,
        voice_id=cfg.get("tts", {}).get("voice_id", "11labs-Adrian"),
        language=cfg.get("language", "en-US"),
        webhook_url=cfg.get("server_url"),
        last_modification_timestamp=ts,
    )


def _format_call(call: CallRun) -> RetellCallResponse:
    start_ts = int(call.started_at.timestamp() * 1000) if call.started_at else 0
    end_ts = int(call.ended_at.timestamp() * 1000) if call.ended_at else None
    dur_ms = int(call.duration_seconds * 1000) if call.duration_seconds else None
    
    status_map = {
        "created": "registered",
        "running": "ongoing",
        "completed": "ended",
        "failed": "error",
    }
    retell_status = status_map.get(call.status, "registered")
    
    return RetellCallResponse(
        call_id=str(call.id),
        agent_id=str(call.agent_id),
        call_status=retell_status,
        from_number=call.caller_number,
        to_number=call.called_number,
        direction=call.call_type or "inbound",
        start_timestamp=start_ts,
        end_timestamp=end_ts,
        duration_ms=dur_ms,
        transcript=call.summary or "",
        recording_url=f"/api/v1/calls/{call.id}/recording" if call.recording_path else None,
    )


# ── Agent Endpoints ──────────────────────────────────────────────────────────

@router.post("/create-agent", response_model=RetellAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_retell_agent(
    req: RetellAgentCreateRequest,
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    model_config = {
        "language": req.language or "en-US",
        "server_url": req.webhook_url,
        "tts": {"provider": "elevenlabs", "voice_id": req.voice_id or "11labs-Adrian"},
        "llm": {"provider": "openai", "model": "gpt-4o-mini"},
        "stt": {"provider": "deepgram", "model": "nova-2"},
        "response_engine": req.response_engine or {"type": "retell-llm"},
    }

    if req.response_engine and req.response_engine.get("type") in ("custom-llm", "custom-websocket"):
        model_config["llm"]["provider"] = "retell-custom-llm"
        model_config["custom_llm_websocket_url"] = req.response_engine.get("url", "")

    agent = Agent(
        org_id=org.id,
        created_by=user.id,
        name=req.agent_name or "Retell Agent",
        model_config=model_config,
        graph={"nodes": [], "edges": []},
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return _format_agent(agent)


@router.get("/get-agent/{agent_id}", response_model=RetellAgentResponse)
async def get_retell_agent(
    agent_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    try:
        aid = int(agent_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    result = await db.execute(select(Agent).where(Agent.id == aid, Agent.org_id == org.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _format_agent(agent)


@router.patch("/update-agent/{agent_id}", response_model=RetellAgentResponse)
async def update_retell_agent(
    agent_id: str,
    req: RetellAgentUpdateRequest,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    try:
        aid = int(agent_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    result = await db.execute(select(Agent).where(Agent.id == aid, Agent.org_id == org.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if req.agent_name is not None:
        agent.name = req.agent_name
    cfg = dict(agent.model_config or {})
    if req.language is not None:
        cfg["language"] = req.language
    if req.voice_id is not None:
        tts_cfg = dict(cfg.get("tts") or {})
        tts_cfg["voice_id"] = req.voice_id
        cfg["tts"] = tts_cfg
    if req.webhook_url is not None:
        cfg["server_url"] = req.webhook_url
    if req.response_engine is not None:
        cfg["response_engine"] = req.response_engine
        if req.response_engine.get("type") in ("custom-llm", "custom-websocket"):
            cfg["llm"] = {"provider": "retell-custom-llm"}
            cfg["custom_llm_websocket_url"] = req.response_engine.get("url", "")
            
    agent.model_config = cfg
    flag_modified(agent, "model_config")
    await db.commit()
    await db.refresh(agent)
    return _format_agent(agent)


@router.delete("/delete-agent/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_retell_agent(
    agent_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    try:
        aid = int(agent_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    result = await db.execute(select(Agent).where(Agent.id == aid, Agent.org_id == org.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await db.delete(agent)
    await db.commit()
    return None


@router.get("/list-agents", response_model=list[RetellAgentResponse])
async def list_retell_agents(
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.org_id == org.id))
    agents = result.scalars().all()
    return [_format_agent(a) for a in agents]


# ── Call Endpoints ───────────────────────────────────────────────────────────

@router.post("/create-web-call", response_model=RetellWebCallResponse, status_code=status.HTTP_201_CREATED)
async def create_retell_web_call(
    req: RetellWebCallRequest,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    try:
        aid = int(req.agent_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    result = await db.execute(select(Agent).where(Agent.id == aid, Agent.org_id == org.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    run = CallRun(
        org_id=org.id,
        agent_id=agent.id,
        transport="webrtc",
        call_type="inbound",
        status="created",
        started_at=datetime.now(UTC),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Generate token
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(org.id), "org": org.id, "run_id": run.id})
    
    return RetellWebCallResponse(
        access_token=token,
        call_id=str(run.id),
    )


@router.post("/create-phone-call", response_model=RetellCallResponse, status_code=status.HTTP_201_CREATED)
async def create_retell_phone_call(
    req: RetellPhoneCallRequest,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    try:
        aid = int(req.agent_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    result = await db.execute(select(Agent).where(Agent.id == aid, Agent.org_id == org.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    run = CallRun(
        org_id=org.id,
        agent_id=agent.id,
        transport="telnyx",
        call_type="outbound",
        status="created",
        caller_number=req.from_number,
        called_number=req.to_number,
        started_at=datetime.now(UTC),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    return _format_call(run)


@router.get("/get-call/{call_id}", response_model=RetellCallResponse)
async def get_retell_call(
    call_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    try:
        cid = int(call_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Call not found")
    
    result = await db.execute(select(CallRun).where(CallRun.id == cid, CallRun.org_id == org.id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Call not found")
    return _format_call(run)


@router.get("/list-calls", response_model=list[RetellCallResponse])
async def list_retell_calls(
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CallRun).where(CallRun.org_id == org.id).order_by(CallRun.started_at.desc()))
    runs = result.scalars().all()
    return [_format_call(r) for r in runs]


# ── Phone Number Endpoints ───────────────────────────────────────────────────

@router.post("/create-phone-number", response_model=RetellPhoneNumberResponse, status_code=status.HTTP_201_CREATED)
async def create_retell_phone_number(
    req: RetellPhoneNumberRequest,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    num = req.phone_number or "+18005550199"
    aid = None
    if req.agent_id:
        try:
            aid = int(req.agent_id)
        except ValueError:
            pass

    phone = PhoneNumber(
        org_id=org.id,
        agent_id=aid,
        phone_number=num,
        label="Retell Number",
    )
    db.add(phone)
    await db.commit()
    await db.refresh(phone)

    return RetellPhoneNumberResponse(
        phone_number=num,
        phone_number_pretty=num,
        agent_id=req.agent_id,
        area_code=req.area_code or 800,
        last_modification_timestamp=int(datetime.now(UTC).timestamp() * 1000),
    )


@router.get("/get-phone-number/{phone_number}", response_model=RetellPhoneNumberResponse)
async def get_retell_phone_number(
    phone_number: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PhoneNumber).where(PhoneNumber.phone_number == phone_number, PhoneNumber.org_id == org.id))
    phone = result.scalar_one_or_none()
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")
    
    return RetellPhoneNumberResponse(
        phone_number=phone.phone_number,
        phone_number_pretty=phone.phone_number,
        agent_id=str(phone.agent_id) if phone.agent_id else None,
        area_code=800,
        last_modification_timestamp=int(datetime.now(UTC).timestamp() * 1000),
    )


@router.delete("/delete-phone-number/{phone_number}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_retell_phone_number(
    phone_number: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PhoneNumber).where(PhoneNumber.phone_number == phone_number, PhoneNumber.org_id == org.id))
    phone = result.scalar_one_or_none()
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")
    
    await db.delete(phone)
    await db.commit()
    return None
