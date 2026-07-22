"""
Auris - Auth routes: signup, login, me
"""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Form, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies.auth import get_current_user, get_current_org
from app.models.organization import OrgMember, Organization, OrgInvite
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
    org_id: int
    email: str
    is_verified: bool
    message: str


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str


@router.post("/register", response_model=SignupResponse, status_code=201)
@router.post("/signup", response_model=SignupResponse, status_code=201)
async def signup(
    body: SignupRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Check email not taken
    existing = await db.execute(select(User).where(User.email == body.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    import random
    import string

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

    # Queue verification email delivery
    from app.services.email_service import send_verification_email
    background_tasks.add_task(send_verification_email, user.email, code)

    return SignupResponse(
        user_id=user.id,
        org_id=org.id,
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

    if user.verification_expires_at and user.verification_expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Verification code has expired")

    user.is_verified = True
    user.verification_code = None
    user.verification_expires_at = None
    await db.commit()

    token = create_access_token(user_id=user.id, org_id=user.selected_org_id)
    return TokenResponse(access_token=token, user_id=user.id, org_id=user.selected_org_id)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    from app.services.structured_logging import log_auth_failure, StructuredLogger, LogLevel
    
    email_val = None
    pass_val = None
    content_type = request.headers.get("content-type", "")
    ip_address = request.client.host if request.client else None
    
    if "application/json" in content_type:
        try:
            data = await request.json()
            email_val = data.get("email")
            pass_val = data.get("password")
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            email_val = form.get("username") or form.get("email")
            pass_val = form.get("password")
        except Exception:
            pass

    if not email_val or not pass_val:
        log_auth_failure("Missing credentials", ip_address=ip_address)
        raise HTTPException(status_code=400, detail="Email and password are required")

    result = await db.execute(select(User).where(User.email == email_val.lower()))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(pass_val, user.password_hash):
        log_auth_failure("Invalid email or password", ip_address=ip_address, email=email_val)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        log_auth_failure("Account deactivated", ip_address=ip_address, user_id=user.id)
        raise HTTPException(status_code=403, detail="Account is deactivated")

    if not user.is_verified:
        log_auth_failure("Email not verified", ip_address=ip_address, user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in."
        )

    token = create_access_token(user_id=user.id, org_id=user.selected_org_id)
    StructuredLogger.log_auth_success(user.id, user.selected_org_id, method="password")
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


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"


class AcceptInviteRequest(BaseModel):
    token: str
    password: str | None = None
    full_name: str | None = None


class MemberResponse(BaseModel):
    user_id: int
    email: str
    full_name: str | None
    role: str
    joined_at: datetime


class SelectOrgRequest(BaseModel):
    org_id: int


@router.post("/org/invite", status_code=201)
async def invite_member(
    body: InviteRequest,
    background_tasks: BackgroundTasks,
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify caller role
    caller_member_res = await db.execute(
        select(OrgMember).where(OrgMember.org_id == org.id, OrgMember.user_id == user.id)
    )
    caller_member = caller_member_res.scalar_one_or_none()
    if not caller_member or caller_member.role not in ("owner", "admin"):
         raise HTTPException(status_code=403, detail="Only owners and admins can invite members")

    import secrets
    token = secrets.token_urlsafe(32)
    
    expires_at = datetime.now(UTC) + timedelta(days=7)
    
    invite = OrgInvite(
        org_id=org.id,
        email=body.email.lower(),
        role=body.role,
        token=token,
        expires_at=expires_at,
    )
    db.add(invite)
    await db.commit()
    
    from app.core.config import FRONTEND_URL
    invite_url = f"{FRONTEND_URL}/accept-invite?token={token}"
    
    from app.services.email_service import send_invite_email
    background_tasks.add_task(send_invite_email, body.email.lower(), org.name, invite_url)
    
    return {"message": "Invitation sent successfully", "token": token}


@router.post("/org/accept-invite", response_model=TokenResponse)
async def accept_invite(
    body: AcceptInviteRequest,
    db: AsyncSession = Depends(get_db),
):
    invite_res = await db.execute(select(OrgInvite).where(OrgInvite.token == body.token))
    invite = invite_res.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invitation token")
    if invite.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invitation token has expired")
    if invite.accepted_at is not None:
        raise HTTPException(status_code=400, detail="Invitation already accepted")

    user_res = await db.execute(select(User).where(User.email == invite.email.lower()))
    user = user_res.scalar_one_or_none()
    if not user:
        if not body.password:
            raise HTTPException(status_code=400, detail="Password is required to create a new account")
        user = User(
            email=invite.email.lower(),
            password_hash=hash_password(body.password),
            full_name=body.full_name or invite.email.split('@')[0],
            is_verified=True,
        )
        db.add(user)
        await db.flush()

    mem_res = await db.execute(
        select(OrgMember).where(OrgMember.org_id == invite.org_id, OrgMember.user_id == user.id)
    )
    if mem_res.scalar_one_or_none():
        invite.accepted_at = datetime.now(UTC)
        await db.commit()
        token = create_access_token(user_id=user.id, org_id=invite.org_id)
        return TokenResponse(access_token=token, user_id=user.id, org_id=invite.org_id)

    member = OrgMember(org_id=invite.org_id, user_id=user.id, role=invite.role)
    db.add(member)

    user.selected_org_id = invite.org_id
    invite.accepted_at = datetime.now(UTC)
    await db.commit()

    token = create_access_token(user_id=user.id, org_id=invite.org_id)
    return TokenResponse(access_token=token, user_id=user.id, org_id=invite.org_id)


@router.get("/org/members", response_model=list[MemberResponse])
async def get_org_members(
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(OrgMember, User)
        .join(User, OrgMember.user_id == User.id)
        .where(OrgMember.org_id == org.id)
    )
    members = result.all()
    return [
        MemberResponse(
            user_id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m, u in members
    ]


@router.delete("/org/members/{member_user_id}", status_code=204)
async def remove_org_member(
    member_user_id: int,
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    caller_member_res = await db.execute(
        select(OrgMember).where(OrgMember.org_id == org.id, OrgMember.user_id == user.id)
    )
    caller_member = caller_member_res.scalar_one_or_none()
    if not caller_member or caller_member.role not in ("owner", "admin"):
         raise HTTPException(status_code=403, detail="Only owners and admins can remove members")

    target_member_res = await db.execute(
        select(OrgMember).where(OrgMember.org_id == org.id, OrgMember.user_id == member_user_id)
    )
    target_member = target_member_res.scalar_one_or_none()
    if not target_member:
        raise HTTPException(status_code=404, detail="Member not found in organization")

    if target_member.role == "owner" and caller_member.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can remove other owners")

    await db.delete(target_member)
    await db.commit()


@router.put("/select-org", response_model=TokenResponse)
async def select_org(
    body: SelectOrgRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_res = await db.execute(
        select(OrgMember).where(OrgMember.org_id == body.org_id, OrgMember.user_id == user.id)
    )
    member = member_res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="User is not a member of this organization")

    user.selected_org_id = body.org_id
    await db.commit()

    token = create_access_token(user_id=user.id, org_id=body.org_id)
    return TokenResponse(access_token=token, user_id=user.id, org_id=body.org_id)
