"""
Auris - User model
"""
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)       # nullable for OAuth users
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_code = Column(String(length=6), nullable=True)
    verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Which org this user is currently operating as
    selected_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # Relationships
    selected_org = relationship("Organization", foreign_keys=[selected_org_id])
    memberships = relationship("OrgMember", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")
