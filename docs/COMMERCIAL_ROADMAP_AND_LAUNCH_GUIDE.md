# 👑 Auris Voice AI — Commercial Roadmap & Go-To-Market (GTM) Launch Guide

This document details the complete commercial architecture, required third-party API integrations, production cloud deployment specifications, and go-to-market strategy to publicly promote **Auris** as an enterprise-grade competitor to **Retell AI** and **Vapi**.

---

## 🗺️ 1. Executive Summary & Platform Capabilities

**Auris** is a turnkey, self-hosted Conversational Voice AI SaaS platform. Unlike proprietary competitors where businesses pay high per-minute markups and risk platform lock-in, Auris gives founders **100% codebase ownership** and complete control over their speech data, telephony carriers, and LLM orchestration.

### Key Platform Highlights
- **Custom Pipecat Engine**: Frame-based real-time audio pipeline processing sub-second STT $\rightarrow$ LLM $\rightarrow$ TTS streaming with natural interruption handling (barge-in) and endpointing.
- **Visual Workflow Builder**: Interactive React Flow 12 canvas studio supporting custom conversation tree nodes (`agent`, `startCall`, `endCall`, `webhook`, `qa`, `tuner`), edge branching, and cycle validation.
- **Knowledge Base RAG**: Ingestion pipeline for PDF/TXT/DOCX uploads up to 100MB, pgvector 1536-dimensional semantic indexing, and real-time prompt injection during active calls.
- **Outbound Dialer Campaigns**: Bulk contact CSV upload manager (`POST /campaign/upload`), asynchronous `ARQ` background worker dispatching, and Redis token-bucket per-tenant rate limiting.
- **Repeat Caller Memory**: Automated customer phone number tracking and dynamic injected conversation summaries.
- **Pre-Paid SaaS Billing**: Native Razorpay credit top-ups (`₹1 = 1 credit`), HMAC webhook signature validation, and atomic balance deductions.

---

## ⚔️ 2. Competitive Parity Matrix: Auris vs. Retell AI & Vapi

| Capability | Retell AI / Vapi | 🟢 Auris Voice AI Platform |
| :--- | :--- | :--- |
| **Conversational Latency** | ~600ms – 1200ms WebRTC | **< 600ms Custom Frame Engine**: Optimized async streaming buffers via `Pipecat` & Deepgram Nova-2. |
| **Flow Studio** | Proprietary tree builder | **Open React Flow 12 Studio**: Fully extensible custom React nodes, dagre auto-layouting, and undo/redo history. |
| **SIP Trunk Provisioning** | Limited carrier selection | **Carrier Agnostic SIP / ARI**: Plug in Telnyx, Twilio, Vonage, or Asterisk ARI directly via REST routes. |
| **Document RAG** | Standard vector search | **pgvector Hybrid Search**: Enqueued background chunking workers and dynamic function calling retrieval. |
| **Parallel Outbound Dialer** | Basic batch triggering | **Enterprise Dialer Worker**: Concurrent call slot locks (`SELECT FOR UPDATE SKIP LOCKED`) & Redis rate limits. |
| **Developer Extensibility** | REST API & Webhooks | **Native MCP Server**: Streamable HTTP Model Context Protocol server mounted at `/api/v1/mcp`. |
| **Economics** | $0.08 - $0.30+ per minute | **Pass-Through Economics**: Pay raw wholesale API rates ($0.01 - $0.03/min total) with zero platform markup. |

---

## 🔑 3. Required API Keys & Vendor Integrations

To transition Auris from local testing to live public production, integrate the following developer accounts in your environment configuration (`.env`):

### A. AI & Speech Pipelines (The Voice Engine)
* **Speech-to-Text (STT)**:
  - **Deepgram** (`DEEPGRAM_API_KEY`): *Recommended model: `nova-2-conversationalai` for industry-lowest streaming speech latency.*
* **Large Language Models (LLM)**:
  - **OpenAI** (`OPENAI_API_KEY`): For `gpt-4o` and `gpt-4o-mini` conversational routing.
  - **Anthropic** (`ANTHROPIC_API_KEY`): For complex reasoning via `claude-3-5-sonnet`.
  - **Groq** (`GROQ_API_KEY`): For ultra-high-speed open-source inferencing (`Llama 3 70B`).
* **Text-to-Speech (TTS)**:
  - **Cartesia** (`CARTESIA_API_KEY`): *Recommended for ultra-fast sonic response (< 100ms TTFB).*
  - **ElevenLabs** (`ELEVENLABS_API_KEY`): For hyper-realistic custom human voice clones.

### B. Telephony & Carriers (Phone Numbers & Calls)
* **Telnyx** (`TELNYX_API_KEY` & `TELNYX_PUBLIC_KEY`): Recommended for enterprise SIP trunks, WebRTC media streams, and instant DID phone number purchasing.
* **Twilio** (`TWILIO_ACCOUNT_SID` & `TWILIO_AUTH_TOKEN`): Standard fallback for automated SIP trunk webhooks.

### C. Commercial Billing & Observability
* **Razorpay** (`RAZORPAY_KEY_ID` & `RAZORPAY_KEY_SECRET`): **100% built-in.** Drop in live credentials to enable self-serve customer credit purchasing.
* **Langfuse** (`LANGFUSE_PUBLIC_KEY` & `LANGFUSE_SECRET_KEY`): **100% built-in.** Traces real-time LLM token consumption, latency scores, and conversation transcripts.
* **Sentry** (`SENTRY_DSN`): **100% built-in.** Captures production backend exceptions and worker errors.

---

## ☁️ 4. Production Cloud Deployment Guide

When launching public production hosting (`https://app.yourdomain.com`), decouple local containerized state by provisioning managed cloud resources:

### Infrastructure Architecture
1. **Database (PostgreSQL 17+)**: Provision an AWS RDS, Supabase, or Neon instance. Enable the `pgvector` extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
2. **Background Queue (Redis 7+)**: Provision an AWS ElastiCache, Render Redis, or Upstash instance for `ARQ` task dispatchers.
3. **Audio & File Storage (S3-Compatible)**: Provision an AWS S3 Bucket or Cloudflare R2 Bucket to store call recordings, knowledge base uploads, and CSV recipient files.

### Container Orchestration
Deploy the production stack using `docker-compose.yaml` (or container runtimes like AWS ECS / GCP Cloud Run):
```bash
# 1. Set environment production flags
export DEPLOYMENT_MODE="saas"
export CORS_ALLOWED_ORIGINS="https://app.yourdomain.com"

# 2. Launch production stack
docker compose -f docker-compose.yaml up -d --build

# 3. Apply Alembic schema migrations
docker compose exec api alembic upgrade head
```

---

## 📣 5. Go-To-Market & Promotion Strategy

### Positioning & Messaging Playbook
Promote Auris on **Product Hunt**, **Hacker News**, **LinkedIn**, and **X (Twitter)** with clear value propositions:
* *“We built an open-source, enterprise-grade alternative to Retell AI and Vapi.”*
* *“Build visual voice AI agent workflows, pgvector RAG knowledge bases, and outbound dialer campaigns — 100% self-hosted in your own cloud.”*
* *“Cut your Voice AI SaaS bills by 80% with pass-through carrier and LLM economics.”*

### Commercialization Checklist
- [x] **Developer Documentation**: Connect the included `docs/` Mintlify directory to host public docs at `docs.yourdomain.com`.
- [x] **Website Embed Widget**: Utilize the built-in `/public-embed` API routes to let enterprise customers embed voice customer support widgets on their websites with a single `<script>` tag.
- [x] **Agency / White-Label Distribution**: Package Auris as a dedicated "Voice AI Agency in a Box" where you deploy dedicated tenant instances for enterprise call centers.

---

## 🚀 6. Future Roadmap (Version 2): Selling Phone Numbers from Local Inventory

To avoid querying and renting virtual phone numbers dynamically from carrier APIs (Telnyx/Twilio) on demand, you can pre-purchase phone numbers in bulk and resell them directly to your customers inside the Auris platform.

### A. Database Inventory Table
Create a database table `available_inventory` to store pre-bought phone numbers:
```python
class AvailableInventory(Base):
    __tablename__ = "available_inventory"
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(32), unique=True, nullable=False)
    region = Column(String(64))
    is_leased = Column(Boolean, default=False)
```

### B. Route Replacement: Search available numbers
Replace the live Telnyx/Twilio API search logic inside `phone_numbers.py` to query your local pre-bought table instead:
```python
@router.get("/search")
async def search_available_numbers(area_code: str, db: AsyncSession = Depends(get_db)):
    # Query your own database for unleased numbers matching the area code
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

### C. Route Replacement: Purchase & Lease Line
Inside the `/buy` route of `phone_numbers.py`, instead of triggering a live API call to purchase/lease a number from Telnyx:
1. Lookup the number in `AvailableInventory`.
2. Update the number state: set `is_leased = True`.
3. Create the regular customer `PhoneNumber` mapping and deduct their credits.

