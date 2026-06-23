from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import json

from app.core.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET
from app.dependencies.auth import get_current_user, get_current_org
from app.core.security import verify_razorpay_signature, verify_razorpay_webhook
from app.core.database import get_db, AsyncSessionLocal

from app.models.organization import Organization
from app.models.billing import CreditTransaction

router = APIRouter()

# ---------- Pydantic schemas ----------
class CreateOrderRequest(BaseModel):
    amount_inr: int = Field(..., ge=100, le=4999, description="Amount in INR (₹100–₹4,999)")

class CreateOrderResponse(BaseModel):
    order_id: str
    amount_paise: int
    currency: str = "INR"
    key_id: str

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class VerifyPaymentResponse(BaseModel):
    success: bool
    credits_added: int
    new_balance: int

class CreditTransactionResponse(BaseModel):
    id: int
    org_id: int
    razorpay_order_id: str
    razorpay_payment_id: str | None = None
    amount_paise: int
    credits_added: float
    status: str
    created_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    balance_credits: int
    transactions: list[CreditTransactionResponse]

# ---------- Helper ----------
def _get_razorpay_client():
    try:
        import razorpay
    except ImportError:
        raise HTTPException(status_code=500, detail="Razorpay SDK not installed")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ---------- Endpoints ----------
@router.post("/billing/razorpay/create-order", response_model=CreateOrderResponse)
async def create_order(
    payload: CreateOrderRequest,
    user=Depends(get_current_user),
    org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    client = _get_razorpay_client()
    # Razorpay expects amount in paise
    amount_paise = payload.amount_inr * 100
    razorpay_order = client.order.create({"amount": amount_paise, "currency": "INR", "receipt": f"org-{org.id}"})
    # Store pending credit transaction
    ct = CreditTransaction(
        org_id=org.id,
        amount_paise=amount_paise,
        razorpay_order_id=razorpay_order["id"],
        credits_added=float(payload.amount_inr),
        status="pending",
    )
    db.add(ct)
    await db.commit()
    await db.refresh(ct)
    return CreateOrderResponse(
        order_id=razorpay_order["id"],
        amount_paise=amount_paise,
        key_id=RAZORPAY_KEY_ID,
    )

@router.post("/billing/razorpay/verify-payment", response_model=VerifyPaymentResponse)
async def verify_payment(
    payload: VerifyPaymentRequest,
    user=Depends(get_current_user),
    org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    if not verify_razorpay_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
        RAZORPAY_KEY_SECRET,
    ):
        raise HTTPException(status_code=400, detail="Invalid Razorpay signature")
    # Find pending transaction
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.razorpay_order_id == payload.razorpay_order_id, CreditTransaction.status == "pending")
    )
    ct = result.scalar_one_or_none()
    if ct is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Mark completed and credit org
    ct.status = "completed"
    ct.completed_at = datetime.now(UTC)
    ct.razorpay_payment_id = payload.razorpay_payment_id
    credits = int(ct.credits_added)
    org.balance_credits = (org.balance_credits or 0) + credits
    db.add(org)  # ensure org update is tracked
    await db.commit()
    return VerifyPaymentResponse(success=True, credits_added=credits, new_balance=int(org.balance_credits))

@router.post("/billing/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
):
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay signature header")
    if not verify_razorpay_webhook(body, signature, RAZORPAY_WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    payload = json.loads(body)
    event = payload.get("event")
    if event != "payment.captured":
        return {"status": "ignored", "event": event}
        
    # Extract needed fields
    payment = payload["payload"]["payment"]["entity"]
    order_id = payment.get("order_id")
    payment_id = payment.get("id")
    amount = payment.get("amount")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.razorpay_order_id == order_id, CreditTransaction.status == "pending")
        )
        ct = result.scalar_one_or_none()
        if ct:
            ct.status = "completed"
            ct.completed_at = datetime.now(UTC)
            ct.razorpay_payment_id = payment_id
            credits = amount // 100
            
            # Fetch and update organization
            org_result = await db.execute(
                select(Organization).where(Organization.id == ct.org_id)
            )
            org = org_result.scalar_one_or_none()
            if org:
                org.balance_credits = (org.balance_credits or 0) + credits
                db.add(org)
            await db.commit()
            return {"status": "processed", "credits_added": credits}
            
    return {"status": "unknown_order"}

@router.get("/billing/balance", response_model=BalanceResponse)
async def get_balance(
    user=Depends(get_current_user),
    org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.org_id == org.id)
        .order_by(CreditTransaction.created_at.desc())
    )
    transactions = result.scalars().all()
    return BalanceResponse(balance_credits=int(org.balance_credits or 0), transactions=transactions)

