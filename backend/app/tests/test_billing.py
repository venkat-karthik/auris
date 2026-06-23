import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.billing import CreditTransaction
from app.models.organization import Organization

class MockSessionContext:
    def __init__(self, session):
        self.session = session
    async def __aenter__(self):
        return self.session
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_create_order_success(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org):
    # Mock razorpay client
    mock_razorpay = MagicMock()
    mock_razorpay.order.create.return_value = {
        "id": "order_mock123",
        "amount": 50000,
        "currency": "INR",
        "receipt": f"org-{test_org.id}"
    }

    with patch("app.routes.billing._get_razorpay_client", return_value=mock_razorpay):
        payload = {"amount_inr": 500}
        response = await client.post("/billing/razorpay/create-order", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == "order_mock123"
        assert data["amount_paise"] == 50000

        # Check DB transaction created
        result = await db_session.execute(
            select(CreditTransaction).where(CreditTransaction.razorpay_order_id == "order_mock123")
        )
        ct = result.scalar_one_or_none()
        assert ct is not None
        assert ct.status == "pending"
        assert ct.credits_added == 500.0

@pytest.mark.asyncio
async def test_verify_payment_success(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org):
    # Setup pending transaction in DB
    ct = CreditTransaction(
        org_id=test_org.id,
        razorpay_order_id="order_to_verify",
        amount_paise=10000,
        credits_added=100.0,
        status="pending"
    )
    db_session.add(ct)
    await db_session.commit()

    # Mock security.verify_razorpay_signature to succeed
    with patch("app.routes.billing.verify_razorpay_signature", return_value=True):
        payload = {
            "razorpay_order_id": "order_to_verify",
            "razorpay_payment_id": "pay_xyz123",
            "razorpay_signature": "sig_abc123"
        }
        response = await client.post("/billing/razorpay/verify-payment", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["credits_added"] == 100
        
        # Original balance was 100, now 200
        assert data["new_balance"] == 200

        # Verify DB transaction status updated
        await db_session.refresh(ct)
        assert ct.status == "completed"
        assert ct.razorpay_payment_id == "pay_xyz123"

        # Verify Org balance updated
        await db_session.refresh(test_org)
        assert test_org.balance_credits == 200.0

@pytest.mark.asyncio
async def test_get_balance(client: AsyncClient, auth_headers, db_session: AsyncSession, test_org):
    # Setup transaction
    ct = CreditTransaction(
        org_id=test_org.id,
        razorpay_order_id="order_balance_test",
        amount_paise=25000,
        credits_added=250.0,
        status="completed"
    )
    db_session.add(ct)
    await db_session.commit()

    response = await client.get("/billing/balance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "balance_credits" in data
    assert len(data["transactions"]) >= 1
    assert data["transactions"][0]["razorpay_order_id"] == "order_balance_test"

@pytest.mark.asyncio
async def test_razorpay_webhook_success(client: AsyncClient, db_session: AsyncSession, test_org):
    # Setup pending transaction in DB
    ct = CreditTransaction(
        org_id=test_org.id,
        razorpay_order_id="order_webhook_test",
        amount_paise=5000,
        credits_added=50.0,
        status="pending"
    )
    db_session.add(ct)
    await db_session.commit()

    webhook_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "order_id": "order_webhook_test",
                    "id": "pay_webhook123",
                    "amount": 5000
                }
            }
        }
    }

    # Mock webhook verification
    with (
        patch("app.routes.billing.verify_razorpay_webhook", return_value=True),
        patch("app.routes.billing.AsyncSessionLocal", return_value=MockSessionContext(db_session))
    ):
        headers = {"x-razorpay-signature": "dummy_sig"}
        response = await client.post("/billing/razorpay/webhook", json=webhook_payload, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "processed"

        # Check DB states
        await db_session.refresh(ct)
        assert ct.status == "completed"
        assert ct.razorpay_payment_id == "pay_webhook123"

        # Check Org balance updated (200 + 50 = 250)
        await db_session.refresh(test_org)
        assert test_org.balance_credits == 250.0
