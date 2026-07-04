# @auris/python-sdk (`auris-python`)

Official Python client library for the **Auris Enterprise Voice AI Platform**. Build, test, and deploy ultra-low latency conversational voice agents over telephony & WebRTC with 100% codebase ownership.

---

## 📦 Installation

```bash
pip install auris-python
```

Or install locally from source:
```bash
cd sdk/python-sdk
pip install -e .
```

---

## 🔐 Authentication

Obtain your API key from your Auris organization dashboard or via the `/api/v1/api_keys` endpoint.

```python
import os
from auris import AurisClient

# Initialize client
api_key = os.environ.get("AURIS_API_KEY", "your_api_key_here")
client = AurisClient(api_key=api_key, base_url="http://localhost:8000/api/v1")
```

---

## ✨ Quickstart Examples

### 1. Agent Management
```python
# List all agents
agents = client.agents.list()
print(f"[SUCCESS] Found {len(agents)} agents.")

# Create an agent
new_agent = client.agents.create(
    name="Customer Support Agent",
    system_prompt="You are a helpful customer support representative for Auris.",
    welcome_message="Hello! How can I assist you today?",
    voice_id="cartesia_en_male"
)
print("Created Agent ID:", new_agent.get("id"))
```

### 2. Outbound Calling & Dispatch
```python
# Dispatch an outbound call to an agent
call_run = client.calls.dispatch(
    agent_id=new_agent["id"],
    to_number="+12345678901",
    call_context={"customer_name": "Alice", "account_tier": "Enterprise"}
)
print("Call Dispatched. Run ID:", call_run.get("id"))
```

### 3. Outbound Dialer Campaigns (Bulk Calls)
```python
# Create a bulk dialer campaign
campaign = client.campaigns.create(
    name="Q3 Upgrade Outreach",
    agent_id=new_agent["id"],
    concurrency=5
)

# Upload contact list
contacts = [
    {"phone_number": "+11111111111", "customer_name": "Bob"},
    {"phone_number": "+22222222222", "customer_name": "Charlie"}
]
client.campaigns.upload_contacts(campaign_id=campaign["id"], contacts=contacts)

# Start campaign
client.campaigns.start(campaign_id=campaign["id"])
```

### 4. Knowledge Base (pgvector RAG)
```python
# Upload document for RAG semantic grounding
doc = client.knowledge_base.upload(
    file_path="/path/to/product_guide.pdf",
    title="Product Guide Q3"
)
print("Uploaded Doc ID:", doc.get("id"))
```

### 5. Enterprise Billing (Razorpay)
```python
# Check credit balance
balance = client.billing.get_balance()
print("Current Credits:", balance)
```

---

## 📄 License
MIT License © Auris Voice AI Platform
