# Auris — AI Agent Handoff Document
**For the next AI model continuing this project.**

---

## Who Is Building This

The founder is Venkat Karthik (GitHub: venkat-karthik).
He is building a voice AI platform from scratch — his own, independent product.
He is technically aware but relies on the AI to write the code.
He is determined, moves fast, and wants to own everything 100%.

---

## The Vision & Emotion Behind This

Venkat started with a codebase called **Zovance** (by Zansat Technologies Private Limited,
BSD-2-Clause licensed). He used it to understand the domain, then made a decision:
**he wants to build his own product from scratch** — not because the license doesn't allow it,
but because he wants full ownership, full independence, and full pride in what he builds.

**The product is called Auris.**
- "Auris" = Latin for "ear" — perfect for a voice AI platform.
- Domain: auris.xyz (available, likely purchased or to be purchased)
- The emotion driving this: "I want to build something that destroys the competition —
  not by copying them, but by being genuinely different."

**The differentiation strategy:**
- Indian market first (Hindi, Telugu, Tamil support — competitors don't have this)
- Personal touch (WhatsApp for enterprise orders, not cold checkout flows)
- Per-minute pricing (simple, predictable)
- Customer memory (agent remembers repeat callers — no competitor does this)
- Agent analytics (conversion funnel — no competitor shows this clearly)

**The competitor landscape:**
- Retell, Vapi, OmniDim — all US-focused, English-first, developer-infrastructure plays
- Auris will dominate by going India-first, then global

---

## What Exists Right Now

### Repository 1: `dograh/` (the old Zovance codebase — reference only)
Location: `C:\Users\user\OneDrive\Desktop\dograh\`
This is the Zovance codebase (BSD licensed). It is being used as **reference only**.
Do NOT modify this codebase. Do NOT copy code from it.
It exists so the developer can understand the domain.

Key things to know about it (for domain understanding):
- FastAPI backend in `api/`
- Next.js 15 frontend in `ui/`
- Uses pipecat framework for voice pipeline
- Has Razorpay billing stub already scaffolded (not yet wired)
- Has MPS (Zansat's managed service) dependency — Venkat wants to REMOVE this entirely
- The rebrand from Zovance→Auris was done across all files

### Repository 2: `dograh/auris/` (THE REAL PROJECT — build here)
Location: `C:\Users\user\OneDrive\Desktop\dograh\auris\`
This is the fresh, from-scratch Auris codebase.
**Every line here is written fresh. Zero Zansat code. 100% owned by Venkat.**

---

## What Has Been Built in `auris/`

### Backend (complete foundation)

```
auris/backend/app/
├── core/
│   ├── config.py        ✅ All env vars (DB, Redis, AI keys, Razorpay, TURN)
│   ├── database.py      ✅ Async SQLAlchemy + session factory + get_db dependency
│   └── security.py      ✅ JWT create/decode, password hash/verify, API key gen/hash,
│                            Razorpay HMAC verification
├── models/
│   ├── user.py          ✅ User (email, password_hash, selected_org_id)
│   ├── organization.py  ✅ Organization (name, slug, balance_credits) + OrgMember
│   ├── api_key.py       ✅ ApiKey (key_hash, key_prefix, is_active)
│   ├── agent.py         ✅ Agent (graph JSON, model_config JSON, context_variables)
│   ├── call_run.py      ✅ CallRun (transport, status, duration, cost_usd)
│   └── billing.py       ✅ CreditTransaction (Razorpay order tracking)
├── dependencies/
│   └── auth.py          ✅ get_current_user (Bearer JWT OR X-API-Key header)
│                            get_current_org (from user.selected_org_id)
├── routes/
│   ├── auth.py          ✅ POST /signup, POST /login, GET /me
│   ├── agents.py        ✅ Full CRUD: POST/GET/PUT/DELETE /agents
│   └── calls.py         ✅ GET /calls, GET /calls/{id}, WS /calls/ws/{agent_id}
├── services/pipeline/
│   ├── frame.py         ✅ Frame dataclass + FrameType enum (all frame types defined)
│   ├── base_processor.py ✅ BaseProcessor (async queue-based, run/stop/emit)
│   ├── engine.py        ✅ PipelineEngine (wires processors, runs concurrently)
│   ├── factory.py       ✅ build_pipeline() — picks right STT/LLM/TTS from config
│   ├── stt/
│   │   ├── deepgram_stt.py  ✅ Deepgram WebSocket streaming STT (English)
│   │   └── sarvam_stt.py    ✅ Sarvam REST STT (Hindi, Telugu, Tamil, Kannada)
│   ├── llm/
│   │   ├── openai_llm.py    ✅ OpenAI streaming + tool calls
│   │   └── groq_llm.py      ✅ Groq (Llama) — extends OpenAI with different base_url
│   ├── tts/
│   │   ├── elevenlabs_tts.py ✅ ElevenLabs streaming TTS (English)
│   │   └── sarvam_tts.py    ✅ Sarvam Bulbul v3 TTS (Hindi, Telugu, Tamil)
│   └── transport/
│       └── webrtc_transport.py ✅ WebSocket transport: browser audio ↔ pipeline
└── main.py              ✅ FastAPI app with CORS, all routers mounted at /api/v1
```

### Infrastructure

```
auris/
├── docker-compose.yml   ✅ Postgres 16 + Redis 7 + MinIO + Backend (with hot reload)
├── README.md            ✅ Full docs including WebSocket protocol
└── backend/
    ├── .env.example     ✅ All variables documented
    ├── requirements.txt ✅ All deps pinned
    ├── Dockerfile       ✅
    └── alembic/
        ├── env.py       ✅ Alembic config pointing to app models
        └── versions/
            └── 0001_initial_schema.py ✅ Full initial migration
                (users, organizations, org_members, api_keys,
                 agents, call_runs, credit_transactions)
```

---

## What Is NOT Built Yet (do these next, in order)

### Priority 1 — Razorpay Billing Routes (backend)
File to create: `auris/backend/app/routes/billing.py`

What it needs:
- `POST /api/v1/billing/razorpay/create-order`
  - Auth required (get_current_user + get_current_org)
  - Body: `{ amount_inr: int }` (₹100–₹4,999)
  - Creates Razorpay order via `razorpay.Client(auth=(KEY_ID, KEY_SECRET))`
  - Stores CreditTransaction with status="pending"
  - Returns: `{ order_id, amount_paise, currency: "INR", key_id }`

- `POST /api/v1/billing/razorpay/verify-payment`
  - Auth required
  - Body: `{ razorpay_order_id, razorpay_payment_id, razorpay_signature }`
  - Verifies HMAC using `security.verify_razorpay_signature()`
  - Updates CreditTransaction status → "completed"
  - Adds credits to `org.balance_credits` (1 rupee = 1 credit)
  - Returns: `{ success: true, credits_added, new_balance }`

- `POST /api/v1/billing/razorpay/webhook` (no auth — verified by HMAC)
  - Fallback if browser closes during payment
  - Verifies webhook signature using `security.verify_razorpay_webhook()`
  - On `payment.captured` event → same credit logic as verify-payment

- `GET /api/v1/billing/balance`
  - Returns: `{ balance_credits, transactions: [...] }`

Register this router in `main.py`.

### Priority 2 — Telephony (Telnyx inbound calls)
File to create: `auris/backend/app/services/pipeline/transport/telnyx_transport.py`
File to create: `auris/backend/app/routes/telephony.py`

What it needs:
- Telnyx sends a WebSocket connection when a call comes in
- Route: `WS /api/v1/telephony/ws/telnyx`
- Query params: Telnyx passes `call_control_id` and org/agent routing info
- The transport reads μ-law 8kHz audio from Telnyx, converts to PCM 16kHz,
  pushes into pipeline, receives PCM back, converts to μ-law, sends back
- Audio conversion: use `audioop` (stdlib) for μ-law ↔ PCM conversion
- Also need: `POST /api/v1/telephony/inbound/telnyx` — webhook to accept incoming call
  and return TwiML-equivalent (TeXML) instructing Telnyx to connect WebSocket

### Priority 3 — Frontend (Next.js)
Location: `auris/frontend/`

Stack: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui

Pages needed (in order):
1. `/auth/login` and `/auth/signup` — basic auth forms
2. `/dashboard` — stats overview (total calls, minutes used, credits left)
3. `/agents` — list + create agents
4. `/agents/[id]` — agent editor (simple form first, visual editor later)
5. `/calls` — call history table
6. `/billing` — credit balance + Razorpay buy credits (INR presets: ₹100/250/500/1000/2500)
             — "Buy Credits" button (<₹5000) OR WhatsApp button (≥₹5000 → wa.me/918309827125)
7. `/settings` — org settings, API keys

The billing UI logic was already designed (see below in the Billing UI section).

### Priority 4 — Customer Memory
Table to add: `customer_profiles`
```sql
id, org_id, phone_number (unique per org), 
name, last_call_at, call_count (int),
summary (text), preferences (JSON),
created_at
```
- Pre-call: lookup by caller phone number → inject into LLM system prompt
- Post-call: ARQ background task runs LLM to generate 2-line summary → upsert profile
- Spam guard: only create/update if call_duration > 60s OR call_count > 1

### Priority 5 — ARQ Background Workers
File to create: `auris/backend/app/tasks/`

Tasks needed:
- `process_call_completion(call_run_id)` — upload recording to MinIO, deduct credits from org
- `update_customer_profile(call_run_id)` — LLM summary → upsert customer_profiles
- `WorkerSettings` class for ARQ

---

## Billing UI (already designed — implement in frontend)

### Logic
- Under ₹5,000: Razorpay automated checkout
- ₹5,000+: WhatsApp redirect to +918309827125

### WhatsApp URL format
```
https://wa.me/918309827125?text=Hi%20Auris%20team%21%20I%27d%20like%20to%20purchase%20%E2%82%B9{amount}%20worth%20of%20credits
```

### Preset chips (INR)
₹100, ₹250, ₹500, ₹1,000, ₹2,500

### Flow
1. User picks amount → if <₹5000, call POST /api/v1/billing/razorpay/create-order
2. Open Razorpay modal (load https://checkout.razorpay.com/v1/checkout.js dynamically)
3. On payment.success → call POST /api/v1/billing/razorpay/verify-payment
4. Show "✓ Credits Added" toast + refresh balance

---

## Environment Variables Needed

All documented in `auris/backend/.env.example`. Key ones:

```
DATABASE_URL=postgresql://auris:auris@localhost:5432/auris
REDIS_URL=redis://localhost:6379
JWT_SECRET=<random 64-char string>
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
GROQ_API_KEY=gsk_...
SARVAM_API_KEY=...          ← Hindi/Telugu/Tamil STT+TTS
TELNYX_API_KEY=KEY...       ← Phone calls
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

---

## How to Run What Exists Now

```bash
cd C:\Users\user\OneDrive\Desktop\dograh\auris

# 1. Copy env file
copy backend\.env.example backend\.env
# Edit backend\.env — fill in DATABASE_URL, REDIS_URL, and at least one AI key

# 2. Start infrastructure
docker compose up postgres redis minio -d

# 3. Setup Python
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app --reload --port 8000

# API docs at: http://localhost:8000/api/v1/docs
```

---

## WebSocket Call Protocol (for frontend to implement)

```
ws://localhost:8000/api/v1/calls/ws/{agent_id}?token={jwt}

Browser → Server:
  { "type": "start", "context": { "customer_name": "Raj" } }
  { "type": "audio", "data": "<base64 PCM 16kHz mono>" }
  { "type": "end" }

Server → Browser:
  { "type": "audio", "data": "<base64 PCM>" }
  { "type": "transcript", "text": "...", "final": true }
  { "type": "end" }
```

---

## Agent Model Config Format

When creating/updating an agent, the `model_config_data` field controls the pipeline:

```json
{
  "language": "hi",
  "cost_tier": "standard",
  "stt": {
    "provider": "sarvam",
    "api_key": "optional — uses platform key if omitted"
  },
  "llm": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "optional"
  },
  "tts": {
    "provider": "sarvam",
    "api_key": "optional"
  }
}
```

If `api_key` is omitted, the platform master key from `.env` is used.
If customer provides their own key, it's used instead (BYOK).

---

## Key Design Decisions Made

1. **No pipecat dependency** — pipeline is written from scratch
   (`frame.py`, `base_processor.py`, `engine.py`)

2. **No MPS (Zansat managed service)** — billing is local
   (`organizations.balance_credits`, `credit_transactions` table)

3. **INR pricing** — Razorpay, not Stripe. Indian market first.

4. **Sarvam AI for Indian languages** — first-class, not an afterthought

5. **"Economy/Standard/Premium" cost tiers** — maps to Groq/GPT-4o-mini/GPT-4o

6. **WhatsApp for enterprise orders** — personal touch, +918309827125

7. **Clean naming** — "Agent" (not workflow), "CallRun" (not workflow_run)

---

## What NOT To Do

- Do NOT import or reference anything from `C:\Users\user\OneDrive\Desktop\dograh\api\`
  or `C:\Users\user\OneDrive\Desktop\dograh\ui\` in the new Auris code
- Do NOT use pipecat as a dependency
- Do NOT use MPS / services.auris.xyz for anything
- Do NOT use Stripe — use Razorpay (INR)
- Do NOT make the WhatsApp number configurable — it is hardcoded: +918309827125

---

## The Moto

**"We don't give you tools. We give you an employee."**

Auris is not infrastructure for developers. It's a product for businesses.
A business owner uploads their info, picks a language, and has a working AI
receptionist in 5 minutes. In Hindi. In Telugu. In English.

That's what no one else is doing. That's the gap. That's Auris.

---

## 🚀 Future Development (Version 2): Selling Phone Numbers from Local Inventory

For Version 2 implementation, instead of querying available virtual numbers dynamically from Twilio or Telnyx APIs (which charges you for active phone lines that may sit idle), the platform is designed to sell phone lines from your own pre-purchased inventory.

### 1. Database Model
Store unassigned bulk numbers in a table:
```python
class AvailableInventory(Base):
    __tablename__ = "available_inventory"
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(32), unique=True, nullable=False)
    region = Column(String(64))
    is_leased = Column(Boolean, default=False)
```

### 2. Search Numbers Endpoint (`GET /phone-numbers/search`)
Query the `AvailableInventory` table directly:
```python
@router.get("/search")
async def search_available_numbers(area_code: str, db: AsyncSession = Depends(get_db)):
    query = select(AvailableInventory).where(
        AvailableInventory.is_leased == False,
        AvailableInventory.phone_number.like(f"%{area_code}%")
    )
    result = await db.execute(query)
    inventory_items = result.scalars().all()
    
    return [
        SearchNumbersResponse(
            phone_number=item.phone_number,
            region=item.region,
            monthly_cost_usd=2.00
        ) for item in inventory_items
    ]
```

### 3. Lease Number Endpoint (`POST /phone-numbers/buy`)
Upon success, deduct client balance, create their regular `PhoneNumber` routing mapping, and set `inventory_item.is_leased = True`.

