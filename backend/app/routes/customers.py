from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_org, get_current_user
from app.models.organization import Organization
from app.models.call_run import CallRun

router = APIRouter(prefix="/customers", tags=["Customers"])


class CustomerResponse(BaseModel):
    id: int
    phone_number: str
    name: str | None = None
    total_calls: int = 0
    total_duration_seconds: int = 0
    last_call_at: datetime | None = None
    sentiment_summary: str | None = None
    memory_tags: list[str] = []

    class Config:
        from_attributes = True


@router.get("", response_model=list[CustomerResponse])
async def list_customers(
    org: Organization = Depends(get_current_org),
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List distinct caller profiles across organization call runs."""
    result = await db.execute(
        select(CallRun)
        .where(CallRun.org_id == org.id)
        .order_by(CallRun.created_at.desc())
    )
    runs = result.scalars().all()

    # Group by customer_number
    grouped: dict[str, list[CallRun]] = {}
    for run in runs:
        num = run.customer_number or "Unknown"
        if num not in grouped:
            grouped[num] = []
        grouped[num].append(run)

    customers = []
    idx = 1
    for num, call_list in grouped.items():
        total_dur = sum((c.duration_seconds or 0) for c in call_list)
        last_call = max((c.created_at for c in call_list), default=None)
        sentiments = [c.sentiment for c in call_list if c.sentiment]
        dominant_sentiment = max(set(sentiments), key=sentiments.count) if sentiments else "Neutral"
        
        customers.append(CustomerResponse(
            id=idx,
            phone_number=num,
            name=f"Caller {num}",
            total_calls=len(call_list),
            total_duration_seconds=total_dur,
            last_call_at=last_call,
            sentiment_summary=dominant_sentiment,
            memory_tags=["VIP Caller"] if len(call_list) > 3 else ["New Contact"]
        ))
        idx += 1

    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    org: Organization = Depends(get_current_org),
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer profile details by ID."""
    customers = await list_customers(org=org, user=user, db=db)
    for c in customers:
        if c.id == customer_id:
            return c
    if customers:
        return customers[0]
    raise HTTPException(status_code=404, detail="Customer not found")
