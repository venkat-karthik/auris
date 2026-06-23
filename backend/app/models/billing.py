"""
Auris - Billing models (Razorpay credit transactions)
"""
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class CreditTransaction(Base):
    """One row per Razorpay order. Idempotent via unique razorpay_order_id."""
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
                    index=True)

    razorpay_order_id = Column(String(64), nullable=False, unique=True, index=True)
    razorpay_payment_id = Column(String(64), nullable=True)

    # Amount in paise (INR × 100)
    amount_paise = Column(Integer, nullable=False)
    # Credits added = amount_paise / 100 (₹1 = 1 credit)
    credits_added = Column(Float, nullable=False)

    # pending → completed | failed
    status = Column(String, nullable=False, default="pending")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    org = relationship("Organization", back_populates="credit_transactions")
