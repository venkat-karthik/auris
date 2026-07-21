# ⚡ AURIS QUICK REFERENCE GUIDE

One-page cheat sheet for common operations.

---

## 🚀 5-Minute Setup

```bash
# Clone & config
git clone https://github.com/venkat-karthik/auris.git && cd auris
cp backend/.env.example backend/.env  # Add your API keys

# Start services
docker compose up postgres redis minio -d

# Setup Python
cd backend && python3.12 -m venv venv
source venv/bin/activate && pip install -r requirements.txt

# Run migrations & start server
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Then visit**: http://localhost:8000/api/v1/docs

---

## 🔐 Authentication

```bash
# Sign up
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

# Verify (check terminal for code)
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","code":"123456"}'

# Use returned access_token in all requests
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
HEADER="Authorization: Bearer $TOKEN"
```

---

## 🤖 Create & Use Agent

```bash
# Create agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "$HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Bot",
    "description": "Sales agent",
    "graph": {
      "nodes": [
        {"id":"start","type":"startCall","data":{"label":"Start"}},
        {"id":"agent","type":"agent","data":{"systemPrompt":"You are...","model":"gpt-4o"}},
        {"id":"end","type":"endCall","data":{"label":"End"}}
      ],
      "edges": [
        {"source":"start","target":"agent"},
        {"source":"agent","target":"end"}
      ]
    },
    "model_config": {"llm":"gpt-4o","stt":"deepgram-nova-2","tts":"cartesia"}
  }'

# List agents
curl -X GET http://localhost:8000/api/v1/agents -H "$HEADER"

# Make call
curl -X POST http://localhost:8000/api/v1/calls/dispatch \
  -H "$HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": 1,
    "to_number": "+1-555-123-4567",
    "from_number": "+1-555-987-6543",
    "carrier": "telnyx"
  }'
```

---

## 📚 Knowledge Base (RAG)

```bash
# Upload document
curl -X POST http://localhost:8000/api/v1/knowledge-base/upload \
  -H "$HEADER" \
  -F "file=@pricing_guide.pdf" \
  -F "description=Enterprise pricing" \
  -F "agent_id=1"

# List documents
curl -X GET http://localhost:8000/api/v1/knowledge-base -H "$HEADER"

# Delete document
curl -X DELETE http://localhost:8000/api/v1/knowledge-base/5 -H "$HEADER"
```

---

## 📞 Campaigns (Outbound Dialer)

```bash
# Create campaign
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "$HEADER" \
  -H "Content-Type: application/json" \
  -d '{"name":"Q3 Sales","agent_id":1}'

# Upload contacts (CSV)
curl -X POST http://localhost:8000/api/v1/campaigns/1/contacts/upload \
  -H "$HEADER" \
  -F "file=@contacts.csv"
# CSV format: phone_number,name
#+1-555-123-4567,John Doe
#+1-555-234-5678,Jane Smith

# Start campaign
curl -X POST http://localhost:8000/api/v1/campaigns/1/start -H "$HEADER"

# Get stats
curl -X GET http://localhost:8000/api/v1/campaigns/1/stats -H "$HEADER"

# Pause campaign
curl -X POST http://localhost:8000/api/v1/campaigns/1/pause -H "$HEADER"
```

---

## 💳 Billing & Credits

```bash
# Check balance
curl -X GET http://localhost:8000/api/v1/billing/balance -H "$HEADER"

# Create order (₹500)
curl -X POST http://localhost:8000/api/v1/billing/razorpay/create-order \
  -H "$HEADER" \
  -H "Content-Type: application/json" \
  -d '{"amount_inr":500}'

# After payment, verify
curl -X POST http://localhost:8000/api/v1/billing/razorpay/verify-payment \
  -H "$HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "razorpay_order_id":"order_9A33XWu590gUtm",
    "razorpay_payment_id":"pay_9A33XWu590gUtm",
    "razorpay_signature":"signature_hash"
  }'
```

---

## 📊 Analytics & Calls

```bash
# List calls
curl -X GET "http://localhost:8000/api/v1/calls?limit=10" -H "$HEADER"

# Get specific call
curl -X GET http://localhost:8000/api/v1/calls/42 -H "$HEADER"

# Get transcript
curl -X GET http://localhost:8000/api/v1/calls/42/transcript -H "$HEADER"

# Get analysis (sentiment, summary)
curl -X GET http://localhost:8000/api/v1/calls/42/analysis -H "$HEADER"

# Agent analytics
curl -X GET http://localhost:8000/api/v1/analytics/agents -H "$HEADER"

# Call outcomes
curl -X GET http://localhost:8000/api/v1/analytics/call_outcomes -H "$HEADER"
```

---

## ☎️ Phone Numbers

```bash
# List numbers
curl -X GET http://localhost:8000/api/v1/phone-numbers -H "$HEADER"

# Search available
curl -X POST http://localhost:8000/api/v1/phone-numbers/search \
  -H "$HEADER" \
  -H "Content-Type: application/json" \
  -d '{"area_code":"415","country":"US"}'

# Buy number
curl -X POST http://localhost:8000/api/v1/phone-numbers/buy \
  -H "$HEADER" \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+1-415-234-5600","carrier":"telnyx"}'

# Release number
curl -X POST http://localhost:8000/api/v1/phone-numbers/1/release -H "$HEADER"
```

---

## 👥 Organization & Team

```bash
# Invite member
curl -X POST http://localhost:8000/api/v1/organizations/invite \
  -H "$HEADER" \
  -H "Content-Type: application/json" \
  -d '{"email":"colleague@example.com","role":"member"}'

# List members
curl -X GET http://localhost:8000/api/v1/organizations/members -H "$HEADER"

# Remove member
curl -X DELETE http://localhost:8000/api/v1/organizations/members/2 -H "$HEADER"
```

---

## 🔄 Environment Variables (backend/.env)

```bash
# AI Providers
OPENAI_API_KEY=sk-proj-xxxxx
DEEPGRAM_API_KEY=xxxxx
ELEVENLABS_API_KEY=xxxxx
GROQ_API_KEY=xxxxx
SARVAM_API_KEY=xxxxx
CARTESIA_API_KEY=xxxxx

# Telephony
TELNYX_API_KEY=xxxxx
TELNYX_PUBLIC_KEY=xxxxx
TWILIO_ACCOUNT_SID=ACxxxxxx
TWILIO_AUTH_TOKEN=xxxxx

# Payments
RAZORPAY_KEY_ID=rzp_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxx

# Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Database
DATABASE_URL=postgresql://auris:auris@localhost:5432/auris
REDIS_URL=redis://localhost:6379
```

---

## 💰 Quick Cost Reference

| Item | Cost |
|------|------|
| **Per Minute (Standard)** | $0.020 USD (~₹1.65) |
| **Per Minute (Cheap - Groq)** | $0.013 USD (~₹1.07) |
| **Per Minute (Premium)** | $0.032 USD (~₹2.64) |
| **Phone Number/Month** | ₹70 (Telnyx) |
| **Minimum Purchase** | ₹100 |
| **Maximum Purchase** | ₹4,999 |

**Example**: 1000 calls × 5 min × $0.020 = $100 (~₹8,250)

---

## 🐛 Debugging

```bash
# Health check
curl http://localhost:8000/api/v1/health

# View logs
docker logs auris-backend-1 -f

# Check database
docker exec auris-postgres-1 psql -U auris -d auris -c "SELECT * FROM call_runs LIMIT 5;"

# Check Redis
docker exec auris-redis-1 redis-cli KEYS "*"

# View Sentry errors
# Visit: https://sentry.io/organizations/[your-org]/issues
```

---

## 🚨 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| **No OpenAI key** | Add OPENAI_API_KEY to .env |
| **Postgres not running** | `docker compose up postgres -d` |
| **Call not connecting** | Check carrier credentials in .env |
| **Insufficient credits** | Buy credits via billing endpoint |
| **Agent not responding** | Verify LLM API key is valid |
| **Slow TTS** | Switch to ElevenLabs or Cartesia |

---

## 📱 Integration Snippets

### Python SDK Example
```python
import requests

token = "eyJhbGc..."
headers = {"Authorization": f"Bearer {token}"}

# Make outbound call
response = requests.post(
    "http://localhost:8000/api/v1/calls/dispatch",
    headers=headers,
    json={
        "agent_id": 1,
        "to_number": "+1-555-123-4567",
        "from_number": "+1-555-987-6543",
        "carrier": "telnyx"
    }
)
call = response.json()
print(f"Call ID: {call['id']}")
```

### Node.js SDK Example
```javascript
const token = "eyJhbGc...";
const headers = { "Authorization": `Bearer ${token}` };

const response = await fetch("http://localhost:8000/api/v1/calls/dispatch", {
  method: "POST",
  headers: { ...headers, "Content-Type": "application/json" },
  body: JSON.stringify({
    agent_id: 1,
    to_number: "+1-555-123-4567",
    from_number: "+1-555-987-6543",
    carrier: "telnyx"
  })
});
const call = await response.json();
console.log(`Call ID: ${call.id}`);
```

---

## 📚 Full Documentation

- **Workflow Guide**: [WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md)
- **Pricing Guide**: [PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md)
- **Setup Guide**: [STARTUP.md](./STARTUP.md)
- **Documentation Index**: [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)

---

**Last Updated**: July 21, 2026  
**Version**: 1.0.0
