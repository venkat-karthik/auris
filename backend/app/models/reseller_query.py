from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class ResellerQuery(Base):
    __tablename__ = "reseller_queries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    volume = Column(String, nullable=False)
    interest = Column(String, nullable=False)
    use_case = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
