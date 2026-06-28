from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_org, get_current_user
from app.models.organization import Organization
from app.models.api_key import ApiKey
from app.core.security import generate_api_key

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(ApiKeyResponse):
    raw_key: str  # Only returned once on creation


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    payload: ApiKeyCreate,
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate and store a new API Key for the organization."""
    raw, key_hash, prefix = generate_api_key()
    
    key = ApiKey(
        org_id=org.id,
        user_id=user.id,
        name=payload.name,
        key_hash=key_hash,
        key_prefix=prefix,
        is_active=True
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    response = ApiKeyCreatedResponse(
        id=key.id,
        name=key.name,
        key_prefix=key.key_prefix,
        is_active=key.is_active,
        created_at=key.created_at,
        raw_key=raw
    )
    return response


@router.get("", response_model=list[ApiKeyResponse])
async def list_keys(
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List active API Keys for the organization."""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.org_id == org.id, ApiKey.archived_at.is_(None))
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return keys


@router.delete("/{key_id}", status_code=status.HTTP_200_OK)
async def archive_key(
    key_id: int,
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive / revoke an API key."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.org_id == org.id,
            ApiKey.archived_at.is_(None)
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")

    key.is_active = False
    key.archived_at = datetime.now(UTC)
    await db.commit()
    return {"message": "API key successfully revoked", "id": key_id}
