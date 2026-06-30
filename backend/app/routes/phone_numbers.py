import random
import httpx
from typing import List, Optional
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core import config
from app.core.database import get_db
from app.dependencies.auth import get_current_org
from app.models.organization import Organization
from app.models.phone_number import PhoneNumber
from app.models.agent import Agent

router = APIRouter(prefix="/phone-numbers", tags=["Phone Numbers"])


class SearchNumbersResponse(BaseModel):
    phone_number: str
    region: str
    monthly_cost_usd: float


class BuyNumberRequest(BaseModel):
    phone_number: str
    label: Optional[str] = None


class BindNumberRequest(BaseModel):
    agent_id: Optional[int] = None


class PhoneNumberResponse(BaseModel):
    id: int
    phone_number: str
    label: Optional[str]
    is_active: bool
    agent_id: Optional[int]
    agent_name: Optional[str]
    created_at: datetime


@router.get("", response_model=List[PhoneNumberResponse])
async def list_phone_numbers(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """List all virtual phone numbers owned by the current organization."""
    query = select(PhoneNumber).where(PhoneNumber.org_id == org.id)
    result = await db.execute(query)
    numbers = result.scalars().all()

    response = []
    for num in numbers:
        agent_name = None
        if num.agent_id:
            agent_res = await db.execute(select(Agent.name).where(Agent.id == num.agent_id))
            agent_name = agent_res.scalar_one_or_none()
        
        response.append(PhoneNumberResponse(
            id=num.id,
            phone_number=num.phone_number,
            label=num.label,
            is_active=num.is_active,
            agent_id=num.agent_id,
            agent_name=agent_name,
            created_at=num.created_at
        ))
    return response


@router.get("/search", response_model=List[SearchNumbersResponse])
async def search_available_numbers(
    area_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """
    Search available virtual numbers to purchase.
    Queries Telnyx API if configured; otherwise falls back to local mock data.
    """
    if config.TELNYX_API_KEY and not config.TELNYX_API_KEY.startswith("mock"):
        try:
            params = {}
            if area_code:
                params["filter[national_destination_code]"] = area_code
            else:
                params["filter[national_destination_code]"] = "830"
            params["filter[country_code]"] = "US"  # Default to US virtual numbers for search
            params["page[size]"] = 5

            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(
                    "https://api.telnyx.com/v2/available_phone_numbers",
                    headers={"Authorization": f"Bearer {config.TELNYX_API_KEY}"},
                    params=params
                )
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    results = []
                    for item in data:
                        phone_number = item.get("phone_number")
                        region_info = item.get("region_information", {})
                        locality = region_info.get("locality", "Texas")
                        state = region_info.get("state_province", "US")
                        results.append(SearchNumbersResponse(
                            phone_number=phone_number,
                            region=f"{locality}, {state}",
                            monthly_cost_usd=2.00
                        ))
                    if results:
                        return results
                else:
                    logger.error(f"Telnyx numbers search failed: {res.status_code} - {res.text}")
        except Exception as e:
            logger.error(f"Error calling Telnyx search numbers API: {e}")

    # Fallback/Mock behavior for development
    prefix = area_code if area_code and len(area_code) == 3 else "830"
    mock_numbers = []
    
    regions = ["Mumbai, IN", "Delhi, IN", "Bangalore, IN", "Texas, US", "California, US"]
    
    for _ in range(5):
        num_suffix = "".join([str(random.randint(0, 9)) for _ in range(7)])
        mock_numbers.append(SearchNumbersResponse(
            phone_number=f"+91{prefix}{num_suffix}" if prefix.startswith("8") else f"+1{prefix}{num_suffix[:7]}",
            region=random.choice(regions),
            monthly_cost_usd=2.00
        ))
    return mock_numbers


@router.post("/buy", response_model=PhoneNumberResponse)
async def buy_phone_number(
    body: BuyNumberRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """
    Purchase a virtual phone number.
    Deducts monthly cost from credits and registers number in the system.
    """
    # 1. Check if org has enough credits for first month ($2.00 = ~160 credits)
    cost_credits = 160.0
    if org.balance_credits < cost_credits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Leasing a number costs {cost_credits} credits ($2.00 USD) monthly."
        )

    # 2. Check if number is already taken
    taken_res = await db.execute(select(PhoneNumber).where(PhoneNumber.phone_number == body.phone_number))
    if taken_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This phone number is already leased in the system")

    # 3. Provision the number on Telnyx if API key is present, otherwise fall back to mock
    telnyx_id = f"tx_num_{random.randint(100000, 999999)}"
    
    if config.TELNYX_API_KEY and not config.TELNYX_API_KEY.startswith("mock"):
        try:
            order_payload = {
                "phone_numbers": [
                    {"phone_number": body.phone_number}
                ]
            }
            if config.TELNYX_CONNECTION_ID:
                order_payload["connection_id"] = config.TELNYX_CONNECTION_ID

            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.post(
                    "https://api.telnyx.com/v2/number_orders",
                    headers={
                        "Authorization": f"Bearer {config.TELNYX_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=order_payload
                )
                if res.status_code in (200, 201):
                    data = res.json().get("data", {})
                    telnyx_id = data.get("id", telnyx_id)
                    logger.info(f"Successfully ordered number {body.phone_number} via Telnyx. Order ID: {telnyx_id}")
                else:
                    logger.error(f"Telnyx number buy failed: {res.status_code} - {res.text}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Telnyx Number Order failed: {res.text}"
                    )
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error calling Telnyx number order API: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to order phone number from Telnyx: {str(e)}"
            )

    # Deduct credits
    org.balance_credits -= cost_credits

    # Create PhoneNumber record
    num = PhoneNumber(
        org_id=org.id,
        phone_number=body.phone_number,
        label=body.label or "Main Reception Line",
        telnyx_id=telnyx_id,
        is_active=True
    )
    db.add(num)
    await db.commit()
    await db.refresh(num)

    return PhoneNumberResponse(
        id=num.id,
        phone_number=num.phone_number,
        label=num.label,
        is_active=num.is_active,
        agent_id=num.agent_id,
        agent_name=None,
        created_at=num.created_at
    )


@router.put("/{number_id}/bind", response_model=PhoneNumberResponse)
async def bind_phone_number(
    number_id: int,
    body: BindNumberRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Bind a virtual phone number to a conversational voice agent (or unbind if agent_id is null)."""
    # Find number
    num_res = await db.execute(select(PhoneNumber).where(PhoneNumber.id == number_id, PhoneNumber.org_id == org.id))
    num = num_res.scalar_one_or_none()
    if not num:
        raise HTTPException(status_code=404, detail="Phone number not found")

    # Verify agent belongs to this organization
    agent_name = None
    if body.agent_id:
        agent_res = await db.execute(select(Agent).where(Agent.id == body.agent_id, Agent.org_id == org.id))
        agent = agent_res.scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=404, detail="Selected agent not found")
        agent_name = agent.name

    num.agent_id = body.agent_id
    await db.commit()
    await db.refresh(num)

    return PhoneNumberResponse(
        id=num.id,
        phone_number=num.phone_number,
        label=num.label,
        is_active=num.is_active,
        agent_id=num.agent_id,
        agent_name=agent_name,
        created_at=num.created_at
    )


@router.delete("/{number_id}")
async def release_phone_number(
    number_id: int,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Release/delete a leased virtual phone number from the organization."""
    num_res = await db.execute(select(PhoneNumber).where(PhoneNumber.id == number_id, PhoneNumber.org_id == org.id))
    num = num_res.scalar_one_or_none()
    if not num:
        raise HTTPException(status_code=404, detail="Phone number not found")

    await db.delete(num)
    await db.commit()
    return {"status": "ok", "message": f"Successfully released phone number {num.phone_number}"}
