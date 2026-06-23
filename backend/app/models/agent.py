"""
Auris - Agent model
An Agent is what the user builds: a voice AI with a name, prompt, and config.
Called "workflow" in competitors. We call it "agent" — cleaner.
"""
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC),
                        onupdate=lambda: datetime.now(UTC))

    # The conversation graph: nodes + edges (JSON)
    # Each node: { id, type, prompt, transitions, tools, ... }
    graph = Column(JSON, nullable=False, default=dict)

    # Agent-level AI model config (overrides org defaults)
    # { llm: {provider, model, api_key}, stt: {...}, tts: {...} }
    model_config = Column(JSON, nullable=False, default=dict)

    # Template variables that callers can inject at call start
    # { "customer_name": "", "order_id": "" }
    context_variables = Column(JSON, nullable=False, default=dict)

    # Relationships
    org = relationship("Organization", back_populates="agents")
    call_runs = relationship("CallRun", back_populates="agent")
