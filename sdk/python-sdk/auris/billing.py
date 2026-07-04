from typing import Optional, Dict, Any

class BillingModule:
    def __init__(self, client):
        self.client = client

    def get_balance(self) -> Dict[str, Any]:
        """Get current credit balance."""
        return self.client.get("billing/balance")

    def create_order(self, amount: int, credits: int) -> Dict[str, Any]:
        """Create a Razorpay payment order for purchasing credits."""
        return self.client.post("billing/razorpay/create-order", json_data={"amount": amount, "credits": credits})

    def verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> Dict[str, Any]:
        """Verify a Razorpay payment signature after top-up."""
        data = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }
        return self.client.post("billing/razorpay/verify-payment", json_data=data)
