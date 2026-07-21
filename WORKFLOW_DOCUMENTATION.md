# 🎯 AURIS VOICE AI PLATFORM - COMPLETE WORKFLOW DOCUMENTATION

**Version:** 1.0.0  
**Last Updated:** July 2026  
**Platform:** Conversational Voice AI SaaS - Enterprise Grade  
**Ownership:** 100% Owned by Venkat Karthik & Zovance

---

## 📑 Table of Contents

1. [Platform Overview](#platform-overview)
2. [Quick Start Guide](#quick-start-guide)
3. [Complete Workflow Diagram](#complete-workflow-diagram)
4. [Core Concepts & Architecture](#core-concepts--architecture)
5. [Pricing & Cost Structure](#pricing--cost-structure)
6. [API Endpoints Reference](#api-endpoints-reference)
7. [Step-by-Step Workflows](#step-by-step-workflows)
8. [Integration Guide](#integration-guide)
9. [Troubleshooting & FAQ](#troubleshooting--faq)

---

## 🌟 Platform Overview

### What is Auris?

Auris is an **enterprise-grade Conversational Voice AI SaaS platform** that enables businesses to:

- **Build AI Voice Agents** with visual workflow studio (React Flow 12)
- **Deploy at Scale** over Telephony (SIP, Telnyx, Twilio) and WebRTC
- **Own 100% of Data** - sub-second latency pipeline, no vendor lock-in
- **Monetize Efficiently** - wholesale pass-through economics ($0.01-$0.03/min vs competitors $0.08-$0.30/min)
- **Leverage RAG** - pgvector knowledge base with semantic document ingestion
- **Run Outbound Campaigns** - parallel dialer with CSV contact upload and Redis rate limiting

### Key Differentiators vs. Retell AI / Vapi

| Feature | Retell/Vapi | **Auris** |
|---------|-------------|---------|
| **Ownership** | Closed-source SaaS | 100% open, deployable in your VPC |
| **Cost/Minute** | $0.08–$0.30+ | $0.01–$0.03 (80%+ margin improvement) |
| **Workflow Builder** | Vendor lock-in | React Flow 12, fully extensible |
| **Carrier Choice** | Vendor SIP only | Bring any: Telnyx, Twilio, Vonage, custom SIP |
| **RAG Capability** | Basic search | pgvector semantic chunking with embeddings |
| **Observability** | Vendor dashboard | Langfuse + Sentry integration |

---

## 🚀 Quick Start Guide

### Prerequisites
- Docker & Docker Compose
- Python 3.12 (not 3.13/3.14)
- API keys (OpenAI, Deepgram, Razorpay, Telnyx/Twilio)

### 5-Minute Setup

```bash
# 1. Clone repository
git clone https://github.com/venkat-karthik/auris.git
cd auris

# 2. Start Docker containers (Postgres + pgvector, Redis, MinIO)
docker compose up postgres redis minio -d

# 3. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# 4. Setup Python environment
cd backend
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. Run migrations
alembic upgrade head

# 6. Start API server
uvicorn app.main:app --reload --port 8000
```

### Verify Installation
- **Health Check**: http://localhost:8000/api/v1/health
- **Swagger Docs**: http://localhost:8000/api/v1/docs
- **Sign Up**: Use Swagger to call `POST /api/v1/auth/signup`
- **Verify Code**: Check terminal logs for 6-digit code, call `POST /api/v1/auth/verify`

---

## 📊 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AURIS VOICE AI PLATFORM                              │
│                      COMPLETE REQUEST FLOW DIAGRAM                          │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │ Mobile/Web   │
                         │ Browser      │
                         └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                ┌───▼────┐  ┌───▼────┐  ┌──▼────┐
                │ Signup │  │ Create │  │ Make  │
                │ & Auth │  │ Agent  │  │ Call  │
                └───┬────┘  └───┬────┘  └──┬────┘
                    │           │           │
                    └───────────┼───────────┘
                                │
                    ┌───────────▼───────────┐
                    │   AURIS BACKEND API   │
                    │   (FastAPI + Python)  │
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
    ┌───▼────┐         ┌───────▼────────┐        ┌────▼───┐
    │ STT    │         │ LLM Pipeline   │        │ TTS    │
    │ Engine │         │ (Agent Logic)  │        │ Engine │
    │ Deepgram│        │ GPT-4o/Groq    │        │Cartesia│
    └───┬────┘         └────────┬───────┘        └────┬───┘
        │                       │                     │
        └───────────────────────┼─────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  CALL ORCHESTRATOR    │
                    │  (Async Frame Engine) │
                    │  <600ms Latency       │
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
    ┌───▼─────────┐   ┌─────────▼────────┐  ┌─────────▼─┐
    │ Telephony   │   │ Knowledge Base   │  │ Analytics │
    │ (SIP/WebRTC)│   │ (pgvector RAG)   │  │ & Logging │
    │ Telnyx      │   │ Semantic Search  │  │(Langfuse) │
    │ Twilio      │   │ Live Injection   │  │(Sentry)   │
    └───┬─────────┘   └─────────┬────────┘  └─────────┬─┘
        │                       │                     │
        └───────────────────────┼─────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   DATA & STORAGE      │
                    │  PostgreSQL + pgvector│
                    │  Redis (Jobs/Cache)   │
                    │  MinIO (Recordings)   │
                    └───────────────────────┘
```

---

## 🏗️ Core Concepts & Architecture

### 1. **Multi-Tenant Organization Model**

Every user belongs to an **Organization** with:
- **Isolated Data**: Agents, calls, contacts, documents, credits
- **Team Members**: Invite/manage team collaborators
- **API Keys**: Generate scoped API keys for integrations
- **Credit Balance**: Pre-paid credit system (₹1 = 1 credit via Razorpay)

### 2. **Voice Agent Anatomy**

Each **Agent** consists of:
- **Name**: Display name (e.g., "Sales Bot V1")
- **Graph**: Visual workflow (React Flow JSON)
- **Model Config**: LLM, STT, TTS vendor settings
- **Context Variables**: Dynamic injection data (customer name, account info)
- **Status**: Active/inactive

### 3. **Call Execution Pipeline**

Every **Call Run** follows this flow:

```
1. INITIATE → 2. STREAM → 3. PROCESS → 4. CHARGE → 5. STORE
   Inbound/       Audio       LLM         Credits    Recording
   Outbound       Frames      Response    Deducted   & Analysis
```

### 4. **Campaign Dialer Model**

**Outbound Campaigns** execute as:
```
CSV Upload → Parse Contacts → ARQ Worker Queue → 
  Rate Limit (Redis) → Parallel Dialing → Call Tracking
```

### 5. **Knowledge Base RAG Engine**

**Document Ingestion Pipeline**:
```
Upload (PDF/TXT/DOCX) → Chunking Service → 
  Embedding (1536-dim) → pgvector Storage → 
  Live Retrieval During Call
```

---

## 💰 Pricing & Cost Structure

### Credit System

- **1 Credit = ₹1 INR**
- **Minimum Purchase**: ₹100 (100 credits)
- **Maximum Single Purchase**: ₹4,999 (4,999 credits)
- **No Expiration**: Credits remain in account indefinitely
- **Currency**: Indian Rupees (INR) via Razorpay

### Cost Breakdown Per Call

#### Speech Services (Wholesale Pass-Through)
| Component | Cost/Minute | Provider |
|-----------|-----------|----------|
| **STT** (Speech-to-Text) | $0.005 | Deepgram Nova-2 |
| **LLM** (Language Model) | $0.010 | OpenAI GPT-4o |
| **TTS** (Text-to-Speech) | $0.005 | Cartesia |
| **Total Per Minute** | **$0.020** (₹1.65/min) | Direct wholesale |

#### Platform Overhead
- **0% Platform Tax**: No markup on speech services
- **Wholesale Only**: Direct API key integration
- **Competitive Advantage**: 75%+ savings vs. Retell AI ($0.08-$0.30/min)

#### Example Scenarios

**Scenario 1: 100 5-minute Calls**
- Speech Cost: 100 × 5 min × $0.020 = $10 USD (~₹830)
- Platform Fee: ₹0 (wholesale pass-through)
- **Total Credits Needed**: ~830 credits (₹830)
- **Cost to Buy**: ₹830 (1 credit = ₹1)

**Scenario 2: Outbound Campaign - 1,000 Contacts**
- Average Duration: 3 minutes
- Speech Cost: 1,000 × 3 × $0.020 = $60 USD (~₹4,980)
- **Total Credits Needed**: ~5,000 credits
- **Cost to Buy**: ₹5,000 (5 maximum purchases of ₹999 each)

**Scenario 3: Knowledge Base RAG - 50 Document Ingestion**
- Embedding Generation: ~₹0 (one-time, batch process)
- Retrieval During Call: Included in LLM costs
- **Total Credits Needed**: ~250 credits (for 50 × 5-min calls with retrieval)
- **Cost to Buy**: ₹250

### Pricing Plans & Tiers

**NO PLAN TIERING** - Auris operates on a **Pure Pay-As-You-Go model**:

✅ **Enterprise Pay-Per-Minute**
- Buy credits in ₹100–₹4,999 increments
- Spend only what you use
- No monthly minimums
- No hidden fees
- Scale up/down instantly

### Billing Endpoints

```
POST   /api/v1/billing/razorpay/create-order
       → Creates Razorpay order for credit purchase
       
POST   /api/v1/billing/razorpay/verify-payment
       → Verifies payment signature & credits account
       
POST   /api/v1/billing/razorpay/webhook
       → Razorpay payment.captured webhook (async)
       
GET    /api/v1/billing/balance
       → Retrieve current credit balance + transaction history
```

---

## 🔌 API Endpoints Reference

### Authentication Endpoints

#### `POST /api/v1/auth/signup`
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (201):**
```json
{
  "message": "Verification code sent to email",
  "user_id": 1
}
```

**Note**: Verification code sent to terminal logs (development) or email (production).

---

#### `POST /api/v1/auth/verify`
Verify email with 6-digit code.

**Request:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1
}
```

---

#### `POST /api/v1/auth/login`
Login with email & password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "organization_id": 1
}
```

---

#### `GET /api/v1/auth/me`
Get current user profile.

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "organizations": [
    {
      "id": 1,
      "name": "My Company",
      "balance_credits": 500.0,
      "members": 1
    }
  ]
}
```

---

### Agent Management Endpoints

#### `POST /api/v1/agents` (Create Agent)
Create a new voice agent.

**Request:**
```json
{
  "name": "Sales Bot V1",
  "description": "Outbound sales dialer for enterprise accounts",
  "graph": {
    "nodes": [
      {
        "id": "start",
        "type": "startCall",
        "position": {"x": 0, "y": 0},
        "data": {"label": "Start"}
      },
      {
        "id": "agent",
        "type": "agent",
        "position": {"x": 200, "y": 0},
        "data": {
          "label": "Agent",
          "systemPrompt": "You are a friendly sales agent...",
          "model": "gpt-4o"
        }
      }
    ],
    "edges": [
      {"id": "e1", "source": "start", "target": "agent"}
    ]
  },
  "model_config": {
    "llm": "gpt-4o",
    "stt": "deepgram-nova-2",
    "tts": "cartesia"
  },
  "context_variables": {
    "company_name": "Acme Corp",
    "max_duration": 600
  }
}
```

**Response (201):**
```json
{
  "id": 1,
  "org_id": 1,
  "name": "Sales Bot V1",
  "description": "Outbound sales dialer for enterprise accounts",
  "graph": { ... },
  "model_config": { ... },
  "context_variables": { ... }
}
```

---

#### `GET /api/v1/agents`
List all agents for organization.

**Response (200):**
```json
[
  {
    "id": 1,
    "org_id": 1,
    "name": "Sales Bot V1",
    "description": "...",
    "graph": { ... },
    "model_config": { ... },
    "context_variables": { ... }
  }
]
```

---

#### `PUT /api/v1/agents/{agent_id}`
Update agent configuration.

**Request:**
```json
{
  "name": "Sales Bot V2",
  "model_config": {
    "llm": "gpt-4-turbo"
  }
}
```

**Response (200):** Updated agent object

---

#### `DELETE /api/v1/agents/{agent_id}`
Soft-delete agent (mark inactive).

**Response (204):** No content

---

#### `GET /api/v1/agents/{agent_id}/studio`
Get visual workflow graph for React Flow editor.

**Response (200):**
```json
{
  "agent_id": 1,
  "graph": { "nodes": [...], "edges": [...] }
}
```

---

#### `POST /api/v1/agents/{agent_id}/studio`
Save visual workflow from React Flow.

**Request:**
```json
{
  "nodes": [...],
  "edges": [...]
}
```

**Response (200):**
```json
{
  "status": "success",
  "agent_id": 1,
  "graph": { ... }
}
```

---

### Call Management Endpoints

#### `POST /api/v1/calls/dispatch`
Initiate an outbound call (telephony).

**Request:**
```json
{
  "agent_id": 1,
  "to_number": "+1-555-123-4567",
  "from_number": "+1-555-987-6543",
  "carrier": "telnyx"
}
```

**Response (201):**
```json
{
  "id": 42,
  "org_id": 1,
  "agent_id": 1,
  "call_sid": "telnyx_call_123",
  "status": "initiated",
  "from_number": "+1-555-987-6543",
  "to_number": "+1-555-123-4567",
  "created_at": "2026-07-21T10:30:00Z",
  "duration_seconds": 0,
  "cost_usd": 0.0
}
```

---

#### `POST /api/v1/calls/web`
Initiate WebRTC call (browser-to-agent).

**Request:**
```json
{
  "agent_id": 1,
  "customer_phone": "+1-555-123-4567",
  "session_name": "session_001"
}
```

**Response (201):** CallRunResponse with WebRTC credentials

---

#### `GET /api/v1/calls`
List all call runs (with filters).

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Results per page (default: 50)
- `agent_id`: Filter by agent
- `status`: Filter by status (initiated, active, completed, failed)

**Response (200):**
```json
{
  "calls": [
    {
      "id": 42,
      "agent_id": 1,
      "status": "completed",
      "duration_seconds": 125.5,
      "cost_usd": 0.042,
      "disposition": "success",
      "voicemail": false,
      "created_at": "2026-07-21T10:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

---

#### `GET /api/v1/calls/{call_id}`
Get detailed call information.

**Response (200):** Full CallRunResponse with transcript

---

#### `GET /api/v1/calls/{call_id}/analysis`
Get post-call analysis (sentiment, keywords, summary).

**Response (200):**
```json
{
  "call_id": 42,
  "sentiment": "positive",
  "summary": "Customer inquired about pricing. Agent provided quote...",
  "keywords": ["pricing", "package", "discount"],
  "actionable_items": ["Follow up with customer"]
}
```

---

#### `GET /api/v1/calls/{call_id}/transcript`
Get full call transcript (turn-by-turn dialogue).

**Response (200):**
```json
{
  "call_id": 42,
  "transcript": [
    {
      "speaker": "agent",
      "text": "Hello, this is Auris support team. How can I help you today?",
      "timestamp": 0.5
    },
    {
      "speaker": "customer",
      "text": "Hi, I'd like to know about your pricing plans.",
      "timestamp": 2.1
    }
  ]
}
```

---

#### `POST /api/v1/calls/{call_id}/end`
End an active call.

**Response (200):** Updated CallRunResponse with final metrics

---

#### `POST /api/v1/calls/{call_id}/dtmf`
Send DTMF tone (dial pad number) during call.

**Request:**
```json
{
  "digit": "1"
}
```

**Response (200):**
```json
{
  "status": "dtmf_sent",
  "digit": "1"
}
```

---

#### `POST /api/v1/calls/{call_id}/warm-transfer`
Initiate warm transfer to human agent.

**Request:**
```json
{
  "transfer_to_number": "+1-555-000-1111"
}
```

**Response (200):**
```json
{
  "status": "transfer_initiated",
  "destination": "+1-555-000-1111"
}
```

---

### Knowledge Base (RAG) Endpoints

#### `POST /api/v1/knowledge-base/upload`
Upload document for semantic indexing.

**Request (multipart/form-data):**
- `file`: PDF, TXT, or DOCX document
- `description` (optional): Document description
- `agent_id` (optional): Associate with specific agent

**Response (201):**
```json
{
  "id": 5,
  "name": "pricing_guide.pdf",
  "description": "Comprehensive pricing documentation",
  "file_path": "knowledge_base/1/1721550600.pdf",
  "agent_id": 1,
  "created_at": "2026-07-21T10:30:00Z"
}
```

**Note**: Embedding ingestion happens asynchronously in background workers.

---

#### `POST /api/v1/knowledge-base/scrape`
Scrape and index web page content.

**Request:**
```json
{
  "url": "https://example.com/pricing",
  "agent_id": 1
}
```

**Response (201):** DocumentResponse

---

#### `GET /api/v1/knowledge-base`
List all knowledge base documents.

**Response (200):**
```json
[
  {
    "id": 5,
    "name": "pricing_guide.pdf",
    "description": "...",
    "file_path": "...",
    "agent_id": 1,
    "created_at": "2026-07-21T10:30:00Z"
  }
]
```

---

#### `DELETE /api/v1/knowledge-base/{doc_id}`
Delete document and all its semantic chunks.

**Response (200):**
```json
{
  "message": "Document and chunks successfully deleted",
  "id": 5
}
```

---

### Campaign Management Endpoints

#### `POST /api/v1/campaigns`
Create new outbound dialer campaign.

**Request:**
```json
{
  "name": "Q3 Sales Blitz",
  "agent_id": 1
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Q3 Sales Blitz",
  "agent_id": 1,
  "status": "pending",
  "created_at": "2026-07-21T10:30:00Z"
}
```

---

#### `GET /api/v1/campaigns`
List all campaigns.

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Q3 Sales Blitz",
    "agent_id": 1,
    "status": "pending",
    "created_at": "2026-07-21T10:30:00Z"
  }
]
```

---

#### `POST /api/v1/campaigns/{campaign_id}/contacts/upload`
Upload CSV contact list for campaign.

**Request (multipart/form-data):**
- `file`: CSV file with phone_number, name columns

**CSV Format:**
```
phone_number,name
+1-555-123-4567,John Doe
+1-555-234-5678,Jane Smith
```

**Response (200):**
```json
{
  "message": "Successfully imported 2 contacts into campaign",
  "count": 2
}
```

---

#### `POST /api/v1/campaigns/{campaign_id}/start`
Start dialing campaign contacts.

**Response (200):**
```json
{
  "id": 1,
  "status": "running",
  "name": "Q3 Sales Blitz"
}
```

**Note**: Background ARQ workers begin dialing contacts with Redis rate limiting.

---

#### `POST /api/v1/campaigns/{campaign_id}/pause`
Pause campaign execution.

**Response (200):**
```json
{
  "id": 1,
  "status": "paused"
}
```

---

#### `GET /api/v1/campaigns/{campaign_id}/stats`
Get campaign analytics (contact status breakdown).

**Response (200):**
```json
{
  "campaign_id": 1,
  "name": "Q3 Sales Blitz",
  "status": "running",
  "total_contacts": 1000,
  "pending": 950,
  "in_progress": 30,
  "completed": 15,
  "failed": 5
}
```

---

### Billing & Credits Endpoints

#### `POST /api/v1/billing/razorpay/create-order`
Create Razorpay order for credit purchase.

**Request:**
```json
{
  "amount_inr": 500
}
```

**Response (200):**
```json
{
  "order_id": "order_9A33XWu590gUtm",
  "amount_paise": 50000,
  "currency": "INR",
  "key_id": "rzp_test_xxxxxxxx"
}
```

---

#### `POST /api/v1/billing/razorpay/verify-payment`
Verify payment and credit account.

**Request:**
```json
{
  "razorpay_order_id": "order_9A33XWu590gUtm",
  "razorpay_payment_id": "pay_9A33XWu590gUtm",
  "razorpay_signature": "9ef4dffbfd84f1318f6739a3ce19f9d85851857ae648f114332d8401e0949a"
}
```

**Response (200):**
```json
{
  "success": true,
  "credits_added": 500.0,
  "new_balance": 725.0
}
```

---

#### `GET /api/v1/billing/balance`
Get current credit balance and transaction history.

**Response (200):**
```json
{
  "balance_credits": 725.0,
  "transactions": [
    {
      "id": 1,
      "org_id": 1,
      "razorpay_order_id": "order_9A33XWu590gUtm",
      "razorpay_payment_id": "pay_9A33XWu590gUtm",
      "amount_paise": 50000,
      "credits_added": 500.0,
      "status": "completed",
      "created_at": "2026-07-21T10:30:00Z",
      "completed_at": "2026-07-21T10:31:00Z"
    }
  ]
}
```

---

#### `GET /api/v1/billing/transactions`
List all billing transactions.

**Response (200):** Array of CreditTransactionResponse objects

---

### Phone Number & Telephony Endpoints

#### `GET /api/v1/phone-numbers`
List all phone numbers provisioned to organization.

**Response (200):**
```json
[
  {
    "id": 1,
    "org_id": 1,
    "phone_number": "+1-555-123-4567",
    "carrier": "telnyx",
    "status": "active",
    "monthly_cost_usd": 1.50,
    "created_at": "2026-07-21T10:30:00Z"
  }
]
```

---

#### `POST /api/v1/phone-numbers/search`
Search available phone numbers by area code/country.

**Request:**
```json
{
  "area_code": "415",
  "country": "US",
  "limit": 10
}
```

**Response (200):**
```json
{
  "available_numbers": [
    "+1-415-234-5600",
    "+1-415-234-5601",
    "+1-415-234-5602"
  ]
}
```

---

#### `POST /api/v1/phone-numbers/buy`
Purchase and provision a phone number.

**Request:**
```json
{
  "phone_number": "+1-415-234-5600",
  "carrier": "telnyx"
}
```

**Response (201):**
```json
{
  "id": 1,
  "org_id": 1,
  "phone_number": "+1-415-234-5600",
  "carrier": "telnyx",
  "status": "active",
  "monthly_cost_usd": 1.50,
  "created_at": "2026-07-21T10:30:00Z"
}
```

---

#### `POST /api/v1/phone-numbers/{phone_id}/release`
Release/unsubscribe from phone number.

**Response (200):**
```json
{
  "message": "Phone number successfully released",
  "phone_id": 1
}
```

---

### Analytics Endpoints

#### `GET /api/v1/analytics/agents`
Get analytics for all agents (call counts, duration, cost, conversion).

**Response (200):**
```json
[
  {
    "agent_id": 1,
    "name": "Sales Bot V1",
    "call_count": 125,
    "avg_duration": 234.5,
    "conversion_rate": 32.5,
    "voicemail_count": 12,
    "total_cost": 2.55
  },
  {
    "agent_id": 2,
    "name": "Support Bot V1",
    "call_count": 89,
    "avg_duration": 156.2,
    "conversion_rate": 45.2,
    "voicemail_count": 5,
    "total_cost": 1.78
  }
]
```

---

#### `GET /api/v1/analytics/call_outcomes`
Get call outcome breakdown (disposition distribution).

**Response (200):**
```json
[
  {
    "outcome": "Voicemail",
    "count": 17
  },
  {
    "outcome": "Success",
    "count": 89
  },
  {
    "outcome": "Failed",
    "count": 12
  },
  {
    "outcome": "No Answer",
    "count": 7
  }
]
```

---

### Organization & Team Endpoints

#### `POST /api/v1/organizations/invite`
Invite team member to organization.

**Request:**
```json
{
  "email": "colleague@example.com",
  "role": "member"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "colleague@example.com",
  "status": "pending",
  "role": "member"
}
```

---

#### `GET /api/v1/organizations/members`
List organization team members.

**Response (200):**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "role": "admin",
    "status": "active"
  },
  {
    "id": 2,
    "email": "colleague@example.com",
    "role": "member",
    "status": "pending"
  }
]
```

---

#### `POST /api/v1/organizations/accept-invite`
Accept team invitation.

**Request:**
```json
{
  "token": "invite_token_xyz"
}
```

**Response (200):**
```json
{
  "status": "accepted",
  "organization_id": 1
}
```

---

#### `DELETE /api/v1/organizations/members/{member_id}`
Remove team member from organization.

**Response (200):**
```json
{
  "message": "Member removed from organization"
}
```

---

### Health & Monitoring Endpoints

#### `GET /api/v1/health`
System health check.

**Response (200):**
```json
{
  "status": "ok",
  "service": "Auris",
  "version": "1.0.0"
}
```

---

## 📋 Step-by-Step Workflows

### Workflow 1: Create Agent & Make First Call

#### Step 1: Sign Up & Authenticate
```bash
# Use Swagger at http://localhost:8000/api/v1/docs
POST /api/v1/auth/signup
{
  "email": "admin@company.com",
  "password": "SecurePass123!"
}
# → Check terminal for verification code (dev) or email (prod)

POST /api/v1/auth/verify
{
  "email": "admin@company.com",
  "code": "123456"
}
# Response: { "access_token": "...", "organization_id": 1 }
```

#### Step 2: Create Agent with Workflow Graph
```bash
POST /api/v1/agents
{
  "name": "Customer Support Bot",
  "description": "Handles support inquiries",
  "graph": {
    "nodes": [
      {
        "id": "start",
        "type": "startCall",
        "data": {"label": "Start Call"}
      },
      {
        "id": "agent",
        "type": "agent",
        "data": {
          "systemPrompt": "You are a helpful customer support specialist...",
          "model": "gpt-4o"
        }
      },
      {
        "id": "end",
        "type": "endCall",
        "data": {"label": "End Call"}
      }
    ],
    "edges": [
      {"source": "start", "target": "agent"},
      {"source": "agent", "target": "end"}
    ]
  },
  "model_config": {
    "llm": "gpt-4o",
    "stt": "deepgram-nova-2",
    "tts": "cartesia"
  }
}
# Response: { "id": 1, "org_id": 1, ... }
```

#### Step 3: Make First Call
```bash
POST /api/v1/calls/dispatch
{
  "agent_id": 1,
  "to_number": "+1-555-123-4567",
  "from_number": "+1-415-555-1234",
  "carrier": "telnyx"
}
# Response: { "id": 1, "status": "initiated", "call_sid": "..." }
```

#### Step 4: Monitor Call Progress
```bash
# Poll for status updates
GET /api/v1/calls/1
# Response: { "status": "active", "duration_seconds": 45.2, ... }

# Get call transcript when complete
GET /api/v1/calls/1/transcript
# Response: { "transcript": [...] }

# Get AI analysis (sentiment, summary)
GET /api/v1/calls/1/analysis
# Response: { "sentiment": "positive", "summary": "..." }
```

#### Step 5: View Billing Impact
```bash
GET /api/v1/billing/balance
# Response: 
# {
#   "balance_credits": 497.5,
#   "transactions": [...]
# }
# Cost deducted: 45.2 sec × ($0.020/60) = 2.5 credits (₹2.50)
```

---

### Workflow 2: Upload Knowledge Base & Inject into Calls

#### Step 1: Create Agent (same as Workflow 1)
```bash
POST /api/v1/agents
{ ... }
# Response: agent_id = 1
```

#### Step 2: Upload Knowledge Base Document
```bash
POST /api/v1/knowledge-base/upload
{
  multipart:
  - file: pricing_guide.pdf
  - description: "Enterprise pricing plans and tier details"
  - agent_id: 1
}
# Response: { "id": 5, "status": "pending_ingestion" }
```

#### Step 3: Wait for Embedding Ingestion
Background workers:
1. Parse PDF/TXT/DOCX
2. Chunk text (max 512 tokens)
3. Generate embeddings (1536-dim via OpenAI)
4. Store in pgvector (fast semantic search)

#### Step 4: Make Call with RAG Injection
```bash
POST /api/v1/calls/dispatch
{
  "agent_id": 1,
  "to_number": "+1-555-123-4567",
  "from_number": "+1-415-555-1234",
  "carrier": "telnyx"
}
```

During call:
- Customer: "What are your pricing plans?"
- LLM retrieves top-3 relevant chunks from pgvector
- LLM injects RAG context into system prompt
- Agent responds with accurate, up-to-date pricing info

#### Step 5: Verify RAG Integration
```bash
GET /api/v1/calls/1/transcript
# See agent responses referencing document content
```

---

### Workflow 3: Launch Outbound Campaign

#### Step 1: Create Campaign
```bash
POST /api/v1/campaigns
{
  "name": "Q3 2026 Sales Outreach",
  "agent_id": 1
}
# Response: { "id": 1, "status": "pending" }
```

#### Step 2: Upload Contact List (CSV)
```bash
POST /api/v1/campaigns/1/contacts/upload
{
  multipart:
  - file: contacts.csv
}

# contacts.csv format:
# phone_number,name
# +1-415-234-5600,Alice Johnson
# +1-415-234-5601,Bob Smith
# +1-415-234-5602,Charlie Davis
```

#### Step 3: Start Campaign
```bash
POST /api/v1/campaigns/1/start
# Response: { "status": "running" }
```

**Behind the scenes:**
1. ARQ background workers poll Redis job queue
2. Redis token bucket ensures rate limit (e.g., 50 calls/min)
3. Worker dials next contact in campaign
4. Call routes to agent (from Step 1)
5. Agent engages customer
6. Call results stored (disposition: success/failed/no_answer/voicemail)

#### Step 4: Monitor Campaign Progress
```bash
GET /api/v1/campaigns/1/stats
# Response:
# {
#   "total_contacts": 1000,
#   "pending": 950,
#   "in_progress": 30,
#   "completed": 15,
#   "failed": 5
# }
```

#### Step 5: Pause or Resume Campaign
```bash
POST /api/v1/campaigns/1/pause
# Response: { "status": "paused" }

POST /api/v1/campaigns/1/start  # Resume
```

#### Step 6: Analyze Campaign Results
```bash
GET /api/v1/analytics/agents
# Response: Agent performance (conversion rate, avg duration, cost)
```

---

### Workflow 4: Provision Phone Numbers & Inbound Calls

#### Step 1: Search Available Numbers
```bash
POST /api/v1/phone-numbers/search
{
  "area_code": "415",
  "country": "US",
  "limit": 5
}
# Response:
# {
#   "available_numbers": [
#     "+1-415-234-5600",
#     "+1-415-234-5601"
#   ]
# }
```

#### Step 2: Buy Phone Number
```bash
POST /api/v1/phone-numbers/buy
{
  "phone_number": "+1-415-234-5600",
  "carrier": "telnyx"
}
# Response:
# {
#   "id": 1,
#   "phone_number": "+1-415-234-5600",
#   "status": "active",
#   "monthly_cost_usd": 1.50
# }
```

#### Step 3: Configure Inbound Routing
In Telnyx/Twilio dashboard:
- Set webhook URL: `https://your-domain.com/api/v1/telephony/inbound/telnyx`
- Configure connection to route calls to Auris

#### Step 4: Receive Inbound Call
Customer calls: +1-415-234-5600
→ Telnyx sends call event to webhook
→ Auris receives and routes to specified agent
→ Agent engages customer

#### Step 5: Review Call Records
```bash
GET /api/v1/calls?status=completed
# Inbound calls appear in call history with full transcripts
```

---

### Workflow 5: Add Team Members & Manage Organization

#### Step 1: Invite Team Member
```bash
POST /api/v1/organizations/invite
{
  "email": "sales_manager@company.com",
  "role": "member"
}
# Response: { "status": "pending" }
```

#### Step 2: Team Member Accepts Invite
Invitation email sent to `sales_manager@company.com`
→ Click link with invite token
→ POST /api/v1/organizations/accept-invite with token
→ Account created and added to organization

#### Step 3: List Team Members
```bash
GET /api/v1/organizations/members
# Response:
# [
#   { "email": "admin@company.com", "role": "admin", "status": "active" },
#   { "email": "sales_manager@company.com", "role": "member", "status": "active" }
# ]
```

#### Step 4: Remove Team Member
```bash
DELETE /api/v1/organizations/members/2
# Response: { "message": "Member removed" }
```

---

## 🔗 Integration Guide

### Integration with Existing Systems

#### Option 1: Direct API Integration (SDK)
Use REST API endpoints directly from your application:

```python
import requests

# Authenticate
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "user@example.com", "password": "SecurePass123!"}
)
access_token = response.json()["access_token"]

# Create agent
headers = {"Authorization": f"Bearer {access_token}"}
agent_data = {
    "name": "My Bot",
    "graph": {...},
    "model_config": {...}
}
response = requests.post(
    "http://localhost:8000/api/v1/agents",
    json=agent_data,
    headers=headers
)
agent_id = response.json()["id"]

# Make call
call_data = {
    "agent_id": agent_id,
    "to_number": "+1-555-123-4567",
    "from_number": "+1-555-987-6543",
    "carrier": "telnyx"
}
response = requests.post(
    "http://localhost:8000/api/v1/calls/dispatch",
    json=call_data,
    headers=headers
)
```

#### Option 2: Generate OpenAPI Client SDK
Auris exposes OpenAPI spec at:
```
http://localhost:8000/api/v1/openapi.json
```

Generate SDKs for multiple languages:
```bash
# Python
openapi-generator-cli generate -i http://localhost:8000/api/v1/openapi.json \
  -g python -o python-sdk

# Node.js
openapi-generator-cli generate -i http://localhost:8000/api/v1/openapi.json \
  -g javascript -o javascript-sdk
```

#### Option 3: Model Context Protocol (MCP)
Mount Auris MCP server at: `http://localhost:8000/api/v1/mcp`

Enables AI agents to call Auris endpoints via standardized MCP interface.

---

### CRM Integration Example

**Scenario**: Sync customer data from Salesforce, inject into calls.

```python
# 1. Fetch customer from Salesforce
sfdc_client = Salesforce()
customer = sfdc_client.get_account("Acme Corp")

# 2. Inject context into agent
auris_headers = {"Authorization": f"Bearer {token}"}
auris_client.update_agent(
    agent_id=1,
    context_variables={
        "customer_name": customer["Name"],
        "account_value": customer["AnnualRevenue"],
        "renewal_date": customer["ContractEndDate"]
    }
)

# 3. Trigger outbound call
auris_client.dispatch_call(
    agent_id=1,
    to_number=customer["Phone"],
    from_number="+1-415-555-1234"
)

# 4. After call, sync results back to Salesforce
call = auris_client.get_call(call_id=42)
sfdc_client.update_task(
    account_id=customer["Id"],
    status=call["disposition"],
    call_notes=call["transcript"]
)
```

---

### Webhooks & Event Hooks

Auris sends event notifications via webhooks:

#### Supported Events
- `call.initiated` - Call started
- `call.completed` - Call finished
- `call.failed` - Call error
- `campaign.started` - Campaign began
- `campaign.completed` - All contacts dialed
- `payment.completed` - Credit purchase confirmed

#### Webhook Configuration
```bash
# Coming soon: Webhook management UI
# For now, configure at: organization settings
```

#### Example Webhook Payload
```json
{
  "event": "call.completed",
  "timestamp": "2026-07-21T10:45:00Z",
  "data": {
    "call_id": 42,
    "agent_id": 1,
    "duration_seconds": 125.5,
    "disposition": "success",
    "cost_usd": 0.042,
    "transcript": [...],
    "sentiment": "positive"
  }
}
```

---

### Carrier Configuration

#### Telnyx Integration

**1. Get Telnyx API Key**
- Visit: https://portal.telnyx.com
- Get: API Key + Public Key

**2. Set Environment Variables**
```bash
# backend/.env
TELNYX_API_KEY=KEY123456789
TELNYX_PUBLIC_KEY=PUBLIC_KEY123
TELNYX_CONNECTION_ID=connection-uuid
TELNYX_CALLER_ID=+1-415-555-0000
```

**3. Create Connection in Telnyx Dashboard**
- Type: Outbound SIP Connection
- Webhook URL: `https://your-domain.com/api/v1/telephony/inbound/telnyx`

**4. Provision Phone Numbers**
```bash
POST /api/v1/phone-numbers/buy
{
  "phone_number": "+1-415-234-5600",
  "carrier": "telnyx"
}
```

#### Twilio Integration

**1. Get Twilio Credentials**
- Visit: https://www.twilio.com/console
- Get: Account SID + Auth Token

**2. Set Environment Variables**
```bash
# backend/.env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
TWILIO_AUTH_TOKEN=auth_token_xxx
TWILIO_CALLER_ID=+1-415-555-0000
```

**3. Configure Twilio Webhook**
- Incoming Calls: `https://your-domain.com/api/v1/telephony/inbound/twilio`
- Message Webhook: `https://your-domain.com/api/v1/whatsapp`

**4. Provision Numbers**
```bash
POST /api/v1/phone-numbers/buy
{
  "phone_number": "+1-415-234-5600",
  "carrier": "twilio"
}
```

---

### AI Vendor Configuration

#### OpenAI (LLM)
```bash
# backend/.env
OPENAI_API_KEY=sk-proj-xxxxx
```
**Cost**: ~$0.01/minute for GPT-4o

#### Deepgram (STT)
```bash
# backend/.env
DEEPGRAM_API_KEY=xxxxx
```
**Cost**: ~$0.005/minute for Nova-2

#### Cartesia (TTS)
```bash
# backend/.env
CARTESIA_API_KEY=xxxxx
```
**Cost**: ~$0.005/minute for voice synthesis

#### Alternative LLMs
- **Groq Llama 3** (cheaper alternative to OpenAI)
- **Anthropic Claude** (more reasoning)
- **Sarvam AI** (Hindi, regional languages)

---

## 🆘 Troubleshooting & FAQ

### Q1: Why is my call not connecting?

**Possible Causes:**
1. **Missing carrier credentials**: Verify TELNYX_API_KEY, TWILIO_ACCOUNT_SID in `.env`
2. **Webhook not configured**: Check carrier dashboard for webhook URL
3. **Invalid phone number**: Ensure number is active and provisioned
4. **LLM API key expired**: Regenerate OPENAI_API_KEY

**Solution:**
```bash
# Test API connectivity
GET /api/v1/health

# Verify agent exists and is active
GET /api/v1/agents/1

# Check billing balance (ensure credits available)
GET /api/v1/billing/balance
```

---

### Q2: How do I reduce costs?

**Strategies:**
1. **Use Groq Llama 3**: ~$0.003/min vs. GPT-4o $0.010/min
2. **Optimize prompt length**: Shorter prompts = fewer tokens
3. **Enable RAG caching**: Reuse embeddings across calls
4. **Batch campaign calls**: Leverage Redis rate limiting
5. **Negotiate carrier rates**: Telnyx/Twilio volume discounts

**Example Cost Comparison:**
- Current: 1,000 calls × 5 min × $0.020 = $100
- With Groq: 1,000 calls × 5 min × $0.010 = $50 (50% savings)

---

### Q3: Why is my agent response slow?

**Typical Latency:**
- STT (speech to text): 100–200ms
- LLM inference: 200–500ms
- TTS (text to speech): 100–300ms
- **Total**: 400–1000ms (< 1 second)

**If exceeding 1.5+ seconds:**
1. Check LLM latency (OpenAI API status page)
2. Reduce system prompt length
3. Switch to faster LLM (Groq)
4. Increase timeout: `model_config.inference_timeout`

---

### Q4: How do I debug a failed call?

```bash
# Get call details
GET /api/v1/calls/42

# Get call transcript (why it ended)
GET /api/v1/calls/42/transcript

# Get error logs
# Check Sentry dashboard (if configured)
```

**Common Failures:**
- `disposition: no_answer` - Customer didn't pick up
- `disposition: failed` - Carrier connection error
- `voicemail: true` - Reached voicemail instead

---

### Q5: Can I use Auris with existing PBX systems?

**Yes!** Auris is carrier-agnostic:

1. **SIP Trunk**: Bring your own SIP provider (not just Telnyx/Twilio)
2. **Asterisk ARI**: Integrate with Asterisk PBX via ARImanager
3. **Custom SIP**: Configure custom SIP trunks in settings

---

### Q6: What happens if my organization runs out of credits?

**Behavior:**
- Active calls: Complete (credits reserved)
- New calls: Rejected with `insufficient_credits` error
- Campaigns: Paused

**Solution:**
```bash
POST /api/v1/billing/razorpay/create-order
{
  "amount_inr": 500
}
# → Credit account & resume operations
```

---

### Q7: How do I export call data?

**Available Exports:**
1. **Transcripts**: `GET /api/v1/calls/{id}/transcript` (JSON/TXT)
2. **Analytics**: `GET /api/v1/analytics/agents` (CSV-compatible)
3. **Recordings**: `GET /api/v1/calls/{id}/recording` (MP3/WAV)
4. **Campaign Results**: Campaign stats export (CSV)

**Example Export (Programmatic):**
```python
calls = auris_client.list_calls(limit=1000)
with open("calls_export.csv", "w") as f:
    for call in calls:
        f.write(f"{call['id']},{call['duration_seconds']},{call['cost_usd']}\n")
```

---

### Q8: How do I monitor costs in real-time?

**Dashboard Overview:**
1. **Organization Dashboard**: Total credits used (YTD)
2. **Agent Analytics**: Cost per agent (`/analytics/agents`)
3. **Call Details**: Per-call cost breakdown
4. **Billing Transactions**: Credit purchase history

**Programmatic Monitoring:**
```bash
# Current balance
GET /api/v1/billing/balance
# → balance_credits: 750.0

# Estimate cost for campaign
campaign_contacts = 1000
avg_duration = 5  # minutes
cost_per_minute = 0.020
total_cost_usd = campaign_contacts * avg_duration * cost_per_minute
total_credits_needed = int(total_cost_usd * 82.5)  # ₹1 ≈ $0.012
```

---

### Q9: How do I set up webhooks for CRM sync?

**Coming in v1.1**:
- Webhook management UI
- Event routing per agent
- Signature verification

**For now**, use polling:
```python
# Poll for completed calls
last_checked = datetime.now()
while True:
    calls = auris_client.list_calls(
        created_after=last_checked,
        status="completed"
    )
    for call in calls:
        crm_client.create_activity(
            contact_id=call.customer_phone,
            notes=call.transcript
        )
    last_checked = datetime.now()
    time.sleep(5)  # Poll every 5 seconds
```

---

### Q10: How is my data stored? Is it encrypted?

**Data Storage:**
- **Calls & Transcripts**: PostgreSQL (encrypted at rest)
- **Recordings**: MinIO/S3 (encrypted at rest)
- **Embeddings**: pgvector (encrypted in transit)

**Encryption:**
- TLS 1.3: In-transit
- AES-256: At-rest (PostgreSQL)
- JWT: Token signing (HS256)

**Data Retention:**
- Call metadata: Indefinite
- Recordings: Configurable (default: 90 days)
- Embeddings: Indefinite (unless document deleted)

---

## 📞 Support & Contact

- **GitHub Issues**: https://github.com/venkat-karthik/auris/issues
- **Email**: support@auris.xyz
- **Slack Community**: (Coming soon)
- **Discord Server**: (Coming soon)

---

## 📜 License

Auris Voice AI Platform is released under the **MIT License**.  
100% owned by Venkat Karthik & Zovance.

**You are free to:**
- ✅ Use commercially
- ✅ Modify the codebase
- ✅ Deploy in your own infrastructure
- ✅ Distribute modified versions
- ✅ Own all call data

**You must:**
- ⚠️ Include license file
- ⚠️ State significant changes

---

## 🚀 Future Roadmap

### v1.1 (Q3 2026)
- [ ] Webhook management UI
- [ ] Advanced RAG chunking strategies
- [ ] Real-time call monitoring dashboard
- [ ] Multi-language support (Spanish, French, German)

### v1.2 (Q4 2026)
- [ ] Video calling (WebRTC)
- [ ] Advanced sentiment analysis
- [ ] Custom metrics & KPIs
- [ ] Audit logging

### v2.0 (Q1 2027)
- [ ] Multi-agent orchestration
- [ ] Advanced workflow branching (QA/Tuner nodes)
- [ ] Real-time translation
- [ ] Enterprise SSO (SAML/OAuth)

---

**Last Updated**: July 21, 2026  
**Maintained By**: Venkat Karthik & Zovance  
**Version**: 1.0.0
