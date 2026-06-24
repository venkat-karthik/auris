"""
Auris - CustomerProfile model for Customer Memory feature.
Stores customer interaction histories, names, summaries, and preferences.
"""
from datetime import UTC, datetime
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base

class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number = Column(String(32), nullable=False, index=True)
    
    name = Column(String, nullable=True)
    last_call_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    call_count = Column(Integer, nullable=False, default=1)
    summary = Column(Text, nullable=True)
    preferences = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Ensure unique customer phone numbers per organization
    __table_args__ = (
        UniqueConstraint("org_id", "phone_number", name="uq_org_customer_phone"),
    )

    org = relationship("Organization")
