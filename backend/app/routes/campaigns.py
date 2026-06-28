from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.dependencies.auth import get_current_org, get_current_user
from app.models.organization import Organization
from app.models.campaign import Campaign, CampaignContact
from app.services.dialer_service import parse_csv_contacts

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CampaignCreate(BaseModel):
    name: str
    agent_id: int


class CampaignResponse(BaseModel):
    id: int
    name: str
    agent_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignStats(BaseModel):
    campaign_id: int
    name: str
    status: str
    total_contacts: int
    pending: int
    in_progress: int
    completed: int
    failed: int


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new outbound dialer campaign."""
    campaign = Campaign(
        org_id=org.id,
        agent_id=payload.agent_id,
        name=payload.name,
        status="pending"
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/contacts/upload", status_code=status.HTTP_200_OK)
async def upload_contacts(
    campaign_id: int,
    file: UploadFile = File(...),
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload contact numbers list via CSV file."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.org_id == org.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    file_data = await file.read()
    try:
        contacts_data = parse_csv_contacts(file_data)
    except Exception as e:
        logger.error(f"Failed to parse CSV contacts: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not contacts_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV does not contain any valid contacts"
        )

    # Insert contacts
    for entry in contacts_data:
        contact = CampaignContact(
            campaign_id=campaign_id,
            phone_number=entry["phone_number"],
            name=entry["name"],
            status="pending"
        )
        db.add(contact)

    await db.commit()
    return {"message": f"Successfully imported {len(contacts_data)} contacts into campaign", "count": len(contacts_data)}


@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: int,
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start campaign dialer execution."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.org_id == org.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = "running"
    await db.commit()

    # Enqueue dialing task on background worker
    try:
        from arq import create_pool
        from arq.connections import RedisSettings
        from app.core.config import REDIS_URL
        redis_settings = RedisSettings.from_dsn(REDIS_URL)
        async def enqueue():
            pool = await create_pool(redis_settings)
            # Enqueue outbound dialer task
            await pool.enqueue_job("dial_next_contacts", campaign_id)
            await pool.close()
        import asyncio
        asyncio.create_task(enqueue())
    except Exception as e:
        logger.error(f"Failed to enqueue campaign dialer background task: {e}")

    return campaign


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: int,
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pause campaign dialer execution."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.org_id == org.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = "paused"
    await db.commit()
    return campaign


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: int,
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed dialer campaign analytics."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.org_id == org.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Aggregate contact statuses
    contacts_select = (
        select(CampaignContact.status, func.count(CampaignContact.id))
        .where(CampaignContact.campaign_id == campaign_id)
        .group_by(CampaignContact.status)
    )
    contacts_result = await db.execute(contacts_select)
    stats_dict = {row[0]: row[1] for row in contacts_result.all()}

    total_count = sum(stats_dict.values())

    return CampaignStats(
        campaign_id=campaign_id,
        name=campaign.name,
        status=campaign.status,
        total_contacts=total_count,
        pending=stats_dict.get("pending", 0),
        in_progress=stats_dict.get("in_progress", 0),
        completed=stats_dict.get("completed", 0),
        failed=stats_dict.get("failed", 0)
    )
