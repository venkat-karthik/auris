"""
Auris - Organization model (multi-tenant)
"""
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)  # url-safe name
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Billing
    balance_credits = Column(Float, nullable=False, default=0.0, server_default="0.0")
    # Price charged to customer per second of call in USD
    price_per_second_usd = Column(Float, nullable=True)

    # Relationships
    members = relationship("OrgMember", back_populates="org")
    agents = relationship("Agent", back_populates="org")
    api_keys = relationship("ApiKey", back_populates="org")
    call_runs = relationship("CallRun", back_populates="org")
    credit_transactions = relationship("CreditTransaction", back_populates="org")
    phone_numbers = relationship("PhoneNumber", back_populates="org", cascade="all, delete-orphan")


class OrgMember(Base):
    """Many-to-many: users ↔ organizations with a role."""
    __tablename__ = "org_members"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False, default="member")  # owner | admin | member
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    org = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")


class OrgInvite(Base):
    """Pending organization invitations sent by email."""
    __tablename__ = "org_invites"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, nullable=False)
    role = Column(String, nullable=False, default="member")  # owner | admin | member
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    org = relationship("Organization")

