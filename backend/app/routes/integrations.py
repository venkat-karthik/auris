from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_org
from app.models.organization import Organization
from app.models.integration import Integration

router = APIRouter(prefix="/integrations", tags=["Integrations"])


class ToggleIntegrationRequest(BaseModel):
    service_name: str
    is_connected: bool
    credentials: Optional[dict] = None


class IntegrationResponse(BaseModel):
    id: int
    service_name: str
    is_connected: bool
    created_at: datetime


@router.get("", response_model=List[IntegrationResponse])
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Retrieve list of connected service integrations for the active organization."""
    query = select(Integration).where(Integration.org_id == org.id)
    result = await db.execute(query)
    items = result.scalars().all()
    return items


@router.post("/toggle", response_model=IntegrationResponse)
async def toggle_integration(
    req: ToggleIntegrationRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Connect or disconnect an integration service."""
    query = select(Integration).where(
        Integration.org_id == org.id,
        Integration.service_name == req.service_name
    )
    result = await db.execute(query)
    integration = result.scalar_one_or_none()

    if not integration:
        integration = Integration(
            org_id=org.id,
            service_name=req.service_name,
            is_connected=req.is_connected,
            credentials=req.credentials
        )
        db.add(integration)
    else:
        integration.is_connected = req.is_connected
        if req.credentials:
            integration.credentials = req.credentials

    await db.commit()
    await db.refresh(integration)
    return integration
