from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_org
from app.models.organization import Organization
from app.models.whatsapp_number import WhatsappNumber
from app.models.agent import Agent

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
