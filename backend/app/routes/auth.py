"""
Auris - Auth routes: signup, login, me
"""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies.auth import get_current_user, get_current_org
from app.models.organization import OrgMember, Organization
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    org_name: str | None = None  # Creates an org on signup if provided


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    org_id: int | None


class MeResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    is_superuser: bool
    selected_org_id: int | None


class SignupResponse(BaseModel):
    user_id: int
    email: str
    is_verified: bool
    message: str


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str


@router.post("/signup", response_model=SignupResponse, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    # Check email not taken
    existing = await db.execute(select(User).where(User.email == body.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    import random
    import string
    from loguru import logger

    code = "".join(random.choices(string.digits, k=6))

    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        is_verified=False,
        verification_code=code,
        verification_expires_at=datetime.now(UTC) + timedelta(minutes=15)
    )
    db.add(user)
    await db.flush()  # Get user.id without commit

    # Auto-create org on signup
    org_name = body.org_name or f"{body.full_name or body.email.split('@')[0]}'s Team"
    slug_base = org_name.lower().replace(" ", "-").replace("'", "")[:40]
    slug = slug_base

    # Ensure unique slug
    counter = 1
    while True:
        taken = await db.execute(select(Organization).where(Organization.slug == slug))
        if not taken.scalar_one_or_none():
            break
        slug = f"{slug_base}-{counter}"
        counter += 1

    org = Organization(name=org_name, slug=slug)
    db.add(org)
    await db.flush()

    member = OrgMember(org_id=org.id, user_id=user.id, role="owner")
    db.add(member)

    user.selected_org_id = org.id
    await db.commit()

    # Log to console so developer can verify locally
    logger.info(f"✉️ [VERIFICATION EMAIL] Code for {user.email}: {code}")

    return SignupResponse(
        user_id=user.id,
        email=user.email,
        is_verified=False,
        message="Verification email sent."
    )


@router.post("/verify", response_model=TokenResponse)
async def verify_code(body: VerifyRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        token = create_access_token(user_id=user.id, org_id=user.selected_org_id)
        return TokenResponse(access_token=token, user_id=user.id, org_id=user.selected_org_id)

    if not user.verification_code or user.verification_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    if user.verification_expires_at and user.verification_expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Verification code has expired")

    user.is_verified = True
    user.verification_code = None
    user.verification_expires_at = None
    await db.commit()

    token = create_access_token(user_id=user.id, org_id=user.selected_org_id)
    return TokenResponse(access_token=token, user_id=user.id, org_id=user.selected_org_id)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in."
        )

    token = create_access_token(user_id=user.id, org_id=user.selected_org_id)
    return TokenResponse(access_token=token, user_id=user.id, org_id=user.selected_org_id)


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)):
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_superuser=user.is_superuser,
        selected_org_id=user.selected_org_id,
    )


class OrganizationUpdate(BaseModel):
    name: str


class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    balance_credits: float

    class Config:
        from_attributes = True


@router.put("/organization", response_model=OrganizationResponse)
async def update_organization(
    payload: OrganizationUpdate,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    org.name = payload.name
    await db.commit()
    await db.refresh(org)
    return org
