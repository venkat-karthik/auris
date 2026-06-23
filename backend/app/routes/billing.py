from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET
from app.dependencies.auth import get_current_user, get_current_org
from app.core.security import verify_razorpay_signature, verify_razorpay_webhook
from app.core.database import get_db
from sqlalchemy.orm import Session

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

class BalanceResponse(BaseModel):
    balance_credits: int
    transactions: list[CreditTransaction]

# ---------- Helper ----------
def _get_razorpay_client():
    try:
        import razorpay
    except ImportError as e:
        raise HTTPException(status_code=500, detail="Razorpay SDK not installed")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ---------- Endpoints ----------
@router.post("/billing/razorpay/create-order", response_model=CreateOrderResponse)
async def create_order(
    payload: CreateOrderRequest,
    user=Depends(get_current_user),
    org=Depends(get_current_org),
    db: Session = Depends(get_db),
):
    client = _get_razorpay_client()
    # Razorpay expects amount in paise
    amount_paise = payload.amount_inr * 100
    razorpay_order = client.order.create({"amount": amount_paise, "currency": "INR", "receipt": f"org-{org.id}"})
    # Store pending credit transaction
    ct = CreditTransaction(
        org_id=org.id,
        amount_paise=amount_paise,
        currency="INR",
        razorpay_order_id=razorpay_order["id"],
        status="pending",
    )
    db.add(ct)
    db.commit()
    db.refresh(ct)
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
    db: Session = Depends(get_db),
):
    if not verify_razorpay_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
        RAZORPAY_KEY_SECRET,
    ):
        raise HTTPException(status_code=400, detail="Invalid Razorpay signature")
    # Find pending transaction
    ct = (
        db.query(CreditTransaction)
        .filter(CreditTransaction.razorpay_order_id == payload.razorpay_order_id, CreditTransaction.status == "pending")
        .first()
    )
    if ct is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    # Mark completed and credit org
    ct.status = "completed"
    credits = ct.amount_paise // 100  # 1 credit per rupee
    org.balance_credits = (org.balance_credits or 0) + credits
    db.commit()
    return VerifyPaymentResponse(success=True, credits_added=credits, new_balance=org.balance_credits)

@router.post("/billing/razorpay/webhook")
async def razorpay_webhook(
    request_body: bytes = Depends(lambda: None),  # placeholder, FastAPI will inject raw body
    razorpay_signature: str = Depends(lambda: None),  # placeholder to read header
):
    # FastAPI does not provide raw body and headers in deps like this; we'll use request directly
    from fastapi import Request
    request: Request = Depends()
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay signature header")
    if not verify_razorpay_webhook(body, signature, RAZORPAY_WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    # Parse JSON payload (simplified)
    import json
    payload = json.loads(body)
    event = payload.get("event")
    if event != "payment.captured":
        return {"status": "ignored", "event": event}
    # Extract needed fields
    payment = payload["payload"]["payment"]["entity"]
    order_id = payment.get("order_id")
    amount = payment.get("amount")
    # Find transaction
    from app.core.database import get_db
    db: Session = next(get_db())
    ct = (
        db.query(CreditTransaction)
        .filter(CreditTransaction.razorpay_order_id == order_id, CreditTransaction.status == "pending")
        .first()
    )
    if ct:
        ct.status = "completed"
        org = db.query(Organization).filter(Organization.id == ct.org_id).first()
        credits = amount // 100
        org.balance_credits = (org.balance_credits or 0) + credits
        db.commit()
        return {"status": "processed", "credits_added": credits}
    return {"status": "unknown_order"}

@router.get("/billing/balance", response_model=BalanceResponse)
async def get_balance(
    user=Depends(get_current_user),
    org=Depends(get_current_org),
    db: Session = Depends(get_db),
):
    transactions = db.query(CreditTransaction).filter(CreditTransaction.org_id == org.id).all()
    return BalanceResponse(balance_credits=org.balance_credits or 0, transactions=transactions)
