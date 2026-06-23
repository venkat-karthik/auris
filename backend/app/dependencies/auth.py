"""
Auris - Auth dependencies for FastAPI routes.
Supports: Bearer JWT token OR X-API-Key header.
"""
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token, hash_api_key
from app.models.api_key import ApiKey
from app.models.organization import Organization
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _get_user_by_id(user_id: int, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def _get_user_by_api_key(raw_key: str, db: AsyncSession) -> User | None:
    key_hash = hash_api_key(raw_key)
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return None
    return await _get_user_by_id(api_key.user_id, db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_api_key: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    # 1. Try X-API-Key header
    if x_api_key:
        user = await _get_user_by_api_key(x_api_key, db)
        if user and user.is_active:
            return user
        raise _UNAUTHORIZED

    # 2. Try Bearer JWT
    if credentials:
        payload = decode_access_token(credentials.credentials)
        if payload:
            user = await _get_user_by_id(int(payload["sub"]), db)
            if user and user.is_active:
                return user

    raise _UNAUTHORIZED


async def get_current_org(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    if not user.selected_org_id:
        raise HTTPException(status_code=400, detail="No organization selected")
    result = await db.execute(
        select(Organization).where(Organization.id == user.selected_org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org
