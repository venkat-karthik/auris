from datetime import UTC, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user, get_current_org
from app.models.organization import Organization, OrgMember, OrgInvite
from app.models.user import User
from app.core.security import create_access_token

router = APIRouter(prefix="/organizations", tags=["Organizations"])


class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    balance_credits: float

    class Config:
        from_attributes = True


class CreateOrgRequest(BaseModel):
    name: str
    slug: str | None = None


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"


class MemberResponse(BaseModel):
    user_id: int
    email: str
    full_name: str | None
    role: str
    joined_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    org_id: int | None


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all organizations the current user is a member of."""
    result = await db.execute(
        select(Organization)
        .join(OrgMember, Organization.id == OrgMember.org_id)
        .where(OrgMember.user_id == user.id)
    )
    orgs = result.scalars().all()
    return orgs


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: CreateOrgRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new organization and assign the creator as owner."""
    slug_base = (payload.slug or payload.name).lower().replace(" ", "-").replace("'", "")[:40]
    slug = slug_base
    counter = 1
    while True:
        taken = await db.execute(select(Organization).where(Organization.slug == slug))
        if not taken.scalar_one_or_none():
            break
        slug = f"{slug_base}-{counter}"
        counter += 1

    org = Organization(name=payload.name, slug=slug, balance_credits=0.0)
    db.add(org)
    await db.flush()

    member = OrgMember(org_id=org.id, user_id=user.id, role="owner")
    db.add(member)
    user.selected_org_id = org.id
    await db.commit()
    await db.refresh(org)
    return org


@router.post("/{org_id}/select", response_model=TokenResponse)
async def select_organization(
    org_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Select active organization and issue new scoped JWT."""
    member_res = await db.execute(
        select(OrgMember).where(OrgMember.org_id == org_id, OrgMember.user_id == user.id)
    )
    member = member_res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="User is not a member of this organization")

    user.selected_org_id = org_id
    await db.commit()

    token = create_access_token(user_id=user.id, org_id=org_id)
    return TokenResponse(access_token=token, user_id=user.id, org_id=org_id)


@router.get("/{org_id}/members", response_model=list[MemberResponse])
async def get_organization_members(
    org_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get members of a specific organization."""
    member_res = await db.execute(
        select(OrgMember).where(OrgMember.org_id == org_id, OrgMember.user_id == user.id)
    )
    if not member_res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized for this organization")

    result = await db.execute(
        select(OrgMember, User)
        .join(User, OrgMember.user_id == User.id)
        .where(OrgMember.org_id == org_id)
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


@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def invite_to_organization(
    body: InviteRequest,
    background_tasks: BackgroundTasks,
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite an email address to the current organization."""
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
