from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, running, paused, completed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    org = relationship("Organization")
    agent = relationship("Agent")
    contacts = relationship("CampaignContact", back_populates="campaign", cascade="all, delete-orphan")


class CampaignContact(Base):
    __tablename__ = "campaign_contacts"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number = Column(String(32), nullable=False)
    name = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)  # pending, in_progress, completed, failed
    call_run_id = Column(Integer, ForeignKey("call_runs.id", ondelete="SET NULL"), nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)

    campaign = relationship("Campaign", back_populates="contacts")
    call_run = relationship("CallRun")
