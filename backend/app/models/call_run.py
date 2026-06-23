"""
Auris - CallRun model
One row per call. Tracks everything about a call from start to finish.
"""
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class CallRun(Base):
    __tablename__ = "call_runs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # How the call was made
    transport = Column(String, nullable=False)   # webrtc | telnyx | twilio | text
    call_type = Column(String, nullable=False)   # inbound | outbound

    # State machine
    # initialized → running → completed | failed
    status = Column(String, nullable=False, default="initialized")

    # Phone numbers
    caller_number = Column(String, nullable=True)
    called_number = Column(String, nullable=True)

    # Timing
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Storage paths
    recording_path = Column(String, nullable=True)
    transcript_path = Column(String, nullable=True)

    # Context injected at call start (template variable values)
    initial_context = Column(JSON, nullable=False, default=dict)

    # Context gathered during the call (LLM extracted info)
    gathered_context = Column(JSON, nullable=False, default=dict)

    # Cost tracking
    cost_usd = Column(Float, nullable=True)
    credits_used = Column(Float, nullable=True)

    # Raw usage stats (token counts, audio seconds per provider)
    usage_stats = Column(JSON, nullable=False, default=dict)

    # Call disposition code (set by agent on completion)
    disposition = Column(String, nullable=True)

    # Relationships
    org = relationship("Organization", back_populates="call_runs")
    agent = relationship("Agent", back_populates="call_runs")
