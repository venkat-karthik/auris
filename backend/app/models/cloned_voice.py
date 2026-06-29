from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClonedVoice(Base):
    __tablename__ = "cloned_voices"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    voice_id = Column(String, nullable=False, unique=True)
    status = Column(String, default="processing", nullable=False)  # processing, ready
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    org = relationship("Organization")
