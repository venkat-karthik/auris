# Auris — Complete Platform Stack: Plans & Prices of Every Tool

> **Every service Auris depends on, what it does, the right paid plan to run without disruption, and the total cost.**

---

## How to Read This

Everything below is split into two groups:

- **AI Layer** — the actual voice pipeline (STT, LLM, TTS, Telephony, Billing)
- **Infrastructure Layer** — the servers, database, cache, storage that keep Auris running

Both are required. Missing either one breaks the platform.

---

## GROUP 1: AI LAYER

---

### 1. Deepgram — English STT

**What it does in Auris:**
Real-time English speech recognition. The `DeepgramSTT` processor opens a persistent WebSocket to `wss://api.deepgram.com/v1/listen` when a call starts, and streams raw 16kHz PCM audio into it continuously. Deepgram fires back word-level transcript tokens in ~200–300ms as the caller speaks. Interim results come in live, final results trigger when 300ms silence is detected (`endpointing=300`). This is the fastest STT path in the entire pipeline.

**Why you can't skip it:**
Every English call goes through this. No Deepgram = no English speech recognition = no English calls.

**Plans:**

| Plan | Monthly Cost | Free Credits | Concurrency Limit | Best For |
|---|---|---|---|---|
| Pay-As-You-Go | $0/month | **$200 free on signup** | 150 WSS streams | Dev & testing |
| **Growth** | **~$333/mo** ($4,000/yr prepaid) | Prepaid credits | **225 WSS streams** | **Production** |
| Enterprise | Custom | Custom | Custom SLAs | High scale |

**Rate:** Nova-2 at **$0.0043/min** (PAYG) → ~$0.0036/min (Growth)

**Recommended plan:** Growth ($4,000/year).
Why: 225 concurrent WebSocket streams. At scale, each live call holds one WebSocket. PAYG's 150 limit means ~150 simultaneous calls max. Growth also includes Standard Uptime SLA — if Deepgram goes down, you get credit.

**Cost at 500 call-hours/month:** 500 × 60 × $0.0043 = **~$129/mo** (covered by Growth plan credits)

---

### 2. Sarvam AI — Hindi/Indian STT + TTS

**What it does in Auris:**
Two processors, one API key:

- **`SarvamSTT`** — Hindi/Telugu/Tamil/Kannada/Marathi/Bengali/Gujarati speech recognition. Buffer-based: audio chunks collect in memory, REST call fires to `https://api.sarvam.ai/speech-to-text` on silence. Model `saarika:v2`. Languages: hi-IN, te-IN, ta-IN, kn-IN, mr-IN, bn-IN, gu-IN, en-IN.

- **`SarvamTTS`** — Indian language voice synthesis. REST call to `https://api.sarvam.ai/text-to-speech`, model `bulbul:v3`. 30+ voices. Returns base64 PCM, decoded and streamed. Voices: meera (Hindi female), pavithra (Telugu female), maya (Tamil female), arjun (English-IN male).

**Why you can't skip it:**
This is Auris's core India-first differentiator. Every Hindi/Indian language call uses Sarvam for both ends. No Sarvam = no Indian language support.

**Pricing (INR, from official docs):**

| Service | Rate |
|---|---|
| STT (saarika:v2) | **₹30/hour = ₹0.50/min** |
| TTS (bulbul:v3) | **₹30 per 10K chars = ₹0.003/char** |
| Free credits | ₹100 on signup |

**Plans (Rate Limits):**

| Plan | Rate Limit | Best For |
|---|---|---|
| Starter | 60 req/min | Dev & testing |
| **Pro** | **200 req/min** | **Early production** |
| **Business** | **1,000 req/min** | **Scaled production** |
| Enterprise | Custom | 150+ concurrent calls |

**Recommended plan:** Start on **Pro** (contact Sarvam for pricing — estimated ₹2,000–5,000/mo based on usage). Upgrade to Business when you hit 20+ simultaneous Indian language calls (Pro's 200 req/min fills up at ~40 concurrent calls firing 5 requests/min each).

**Cost at 500 Hindi call-hours/month:**
- STT: 500 × 60 × ₹0.50 = ₹15,000
- TTS: 500 × 60min × ~500 chars/min × ₹0.003 = ₹45,000
- **Total: ~₹60,000/mo (~$720)**

---

### 3. OpenAI — LLM (Standard/Premium Tiers + Customer Memory)

**What it does in Auris:**
Three roles:

1. **`OpenAILLM` processor** — Standard tier agents (`gpt-4o-mini`) and Premium tier agents (`gpt-4o`). Receives final STT transcript, runs streaming chat completion with full conversation history + system prompt. Supports tool/function calling for agents that do CRM lookups, order queries etc.

2. **`GroqLLM` falls back here** for tool call structure — Groq extends OpenAI class, same API format.

3. **`customer_memory.py`** — Always uses `gpt-4o-mini` to extract caller name, 2-line summary, preferences JSON from every call transcript (post-call background task).

**Pricing (official, June 2026):**

| Model | Input | Output | Cost per call-minute |
|---|---|---|---|
| `gpt-4o-mini` | $0.15/1M tokens | $0.60/1M tokens | ~$0.0001/min |
| `gpt-4o` | $2.50/1M tokens | $10.00/1M tokens | ~$0.0015/min |

**Rate Limit Tiers (automatic, no application needed):**

| Tier | How to Unlock | RPM (4o-mini) | Max Concurrent Calls |
|---|---|---|---|
| Tier 1 | Add credit card | 500 RPM | ~50 |
| **Tier 2** | **Spend $50** | **5,000 RPM** | **~500** |
| Tier 3 | Spend $100 | 5,000 RPM | ~500 |
| Tier 4 | Spend $250 | 10,000 RPM | ~1,000 |
| Tier 5 | Spend $1,000 | 30,000 RPM | ~3,000 |

**Recommended plan:** PAYG — just spend $50 early to unlock Tier 2. Set a monthly budget cap in the dashboard to prevent runaway costs.

**Cost at 500 call-hours/month (Standard tier, GPT-4o-mini):** 500 × 60 × $0.0001 = **~$3/mo** (negligible)

---

### 4. Groq — Economy LLM

**What it does in Auris:**
Economy tier (`cost_tier: "economy"` in agent config). The `GroqLLM` class is identical to `OpenAILLM` — it just points `base_url` to `https://api.groq.com/openai/v1`. Uses Groq's LPU hardware, which delivers first token in <100ms consistently. Model: `llama-4-scout-17b-16e-instruct`.

**Pricing (from groq.com, live data):**

| Model | Input | Output | Speed |
|---|---|---|---|
| **Llama 4 Scout 17Bx16E** | **$0.11/1M** | **$0.34/1M** | 594 TPS |
| Llama 3.1 8B Instant | $0.05/1M | $0.08/1M | 840 TPS |
| Llama 3.3 70B | $0.59/1M | $0.79/1M | 394 TPS |

**Plans:** 100% PAYG. Free tier: no credit card, 30 RPM (fine for dev). Add card for production — no minimum.

**Cost at 500 call-hours/month (Economy tier):** ~$0.0001/min × 500 × 60 = **~$3/mo** (essentially free)

---

### 5. ElevenLabs — English TTS

**What it does in Auris:**
English voice synthesis. The `ElevenLabsTTS` processor receives `LLM_TEXT_COMPLETE` frames and calls `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream`. Model: `eleven_flash_v2_5` (~75ms TTFB). Default voice: Rachel (`21m00Tcm4TlvDq8ikWAM`). Streams 4KB PCM chunks at 16kHz back through the pipeline. This is the **single most expensive component per minute**.

**Pricing (from elevenlabs.io/pricing/api, live data):**

| Model | Rate | Latency |
|---|---|---|
| **eleven_flash_v2_5 (used in Auris)** | **$0.05 per 1K chars** | ~75ms |
| Multilingual v2/v3 | $0.10 per 1K chars | ~250ms |

~500 chars/min of agent speech → **$0.025/min** of TTS cost.

**Subscription Plans:**

| Plan | Monthly | Flash Chars Included | ~Call Minutes Covered | Commercial License |
|---|---|---|---|---|
| Free | $0 | 20,000 | ~40 min | ❌ |
| Starter | $6 | 120,000 | ~240 min | ✅ |
| **Creator** | **$22** | **440,000** | **~880 min (~15 hrs)** | **✅** |
| **Pro** | **$99** | **1,980,000** | **~3,960 min (~66 hrs)** | **✅** |
| Scale | $299 | 5,980,000 | ~11,960 min (~199 hrs) | ✅ |
| Business | $990 | 19,800,000 | ~39,600 min (~660 hrs) | ✅ |

Overage is always **$0.05/1K chars** — same rate, no penalty pricing.

**Recommended plan:** Start **Creator ($22/mo)** for up to ~15 hours/month. Move to **Pro ($99)** when you cross 66 hours/month of English calls. Move to **Scale ($299)** at 200 hours/month.

**Cost at 500 call-hours/month (English calls):** 500 × 60 × $0.025 = **$750/mo** — either Pro + Scale plan or PAYG overage.

---

### 6. Telnyx — Phone Call Infrastructure

**What it does in Auris:**
Handles all actual telephone calls. When someone dials your DID number, Telnyx fires `POST /api/v1/telephony/inbound/telnyx` (webhook), then opens `WS /api/v1/telephony/ws/telnyx` carrying μ-law 8kHz audio. `TelnyxTransport` converts this to 16kHz PCM for the pipeline and converts back on the way out.

**Pricing (from telnyx.com, PAYG):**

| Service | Rate |
|---|---|
| Voice API platform fee | **$0.002/min** (every call) |
| Inbound SIP (US) | **$0.0035/min** |
| Outbound SIP (US) | **$0.007/min** |
| DID phone number (US local) | **$0.79–$1/mo per number** |
| India inbound/outbound | Higher — check portal |

**Total per inbound US call-minute:** $0.0055/min

**Plans:** Pure PAYG — no subscription, no minimum. Fund your balance and enable auto-recharge.

**Setup requirements:**
1. Create Mission Control Portal account
2. Purchase at least 1 DID number for inbound calls
3. Set webhook URL → your backend `/api/v1/telephony/inbound/telnyx`
4. Enable "Call Control" application

**Cost at 500 call-hours/month:** 500 × 60 × $0.0055 = **~$165/mo**

---

### 7. Razorpay — Customer Billing

**What it does in Auris:**
The entire credit billing system. Three routes: create order, verify payment, webhook fallback. HMAC-signed. ₹1 = 1 Auris credit. Customers buy INR credits through Razorpay (₹100–₹4,999 via checkout, ₹5,000+ via WhatsApp). Webhook ensures balance updates even if the browser closes mid-payment.

**Pricing:** 2% + 18% GST per transaction = **~2.36% effective**. No setup fee, no monthly minimum.

**One-time setup:**
1. Complete KYC on Razorpay dashboard (1–3 days)
2. Switch from `rzp_test_` to `rzp_live_` keys
3. Set webhook → `/api/v1/billing/razorpay/webhook`, event: `payment.captured`

---

## GROUP 2: INFRASTRUCTURE LAYER

---

### 8. PostgreSQL — Neon Serverless

**What it does in Auris:**
Primary database. Stores users, organizations, agents, call_runs, credit_transactions, customer_profiles. Also runs the `pgvector` extension for knowledge base embeddings (1536-dim vectors).

**Why Neon over Railway Postgres:**
Neon is serverless (scales to zero when idle, scales up instantly on traffic). Supports pgvector natively. No migration needed as you grow.

**Plans:**

| Plan | Monthly | Compute | Storage | pgvector |
|---|---|---|---|---|
| Free | $0 | 100 CU-hours/mo | 0.5 GB | ✅ |
| **Launch** | **~$19–25/mo** | **$0.106/CU-hour** | **$0.35/GB-month** | **✅** |
| Scale | ~$69+/mo | $0.222/CU-hour | $0.35/GB-month | ✅ |

**Recommended plan:** **Neon Launch (~$19–25/mo).** Gives you: pgvector, autoscaling (0.25–16 CU), configurable scale-to-zero, 7-day history. Handles production workloads easily up to ~10K concurrent queries.

---

### 9. Redis — Upstash Serverless

**What it does in Auris:**
ARQ background job queue (call completion tasks, customer memory updates, outbound dialer). Rate limiting for API and dialer campaigns. Session/token caching.

**Why Upstash over Railway Redis:**
Serverless, HTTPS-native, scales to zero. No instance to maintain.

**Plans:**

| Plan | Monthly | Rate | Best For |
|---|---|---|---|
| Free | $0 | 10,000 commands/day | Dev |
| **Pay-As-You-Go** | **$0/min + $0.20/100K cmds** | Per command | **Early production** |
| Fixed 250MB | **$10/mo** | Unlimited cmds (10K cmd/sec ceiling) | Steady production |

**Recommended plan:** Start **PAYG** ($0.20/100K commands). At 1M commands/month = $2. At 10M commands = $20. Move to **Fixed $10/mo** when commands are predictable and high.

---

### 10. Object Storage — Cloudflare R2

**What it does in Auris:**
Stores call audio recordings, knowledge base file uploads (PDF/TXT/DOCX up to 100MB), outbound dialer CSVs. Replaces the local MinIO container from docker-compose in production. S3-compatible API — zero code changes needed.

**Why R2 over AWS S3:**
$0 egress fees. Serving audio recordings back to users costs nothing. AWS S3 charges $0.09/GB egress.

**Pricing:**

| Resource | Rate |
|---|---|
| Storage | **$0.015/GB-month** |
| Class A ops (PUT, POST) | $4.50/million |
| Class B ops (GET) | $0.36/million |
| **Egress** | **$0.00 (free forever)** |
| Free tier | 10 GB storage, 1M Class A, 10M Class B/month |

**Recommended plan:** PAYG. At 50GB storage + moderate reads: **~$0.75–5/mo**. Essentially free at early scale.

---

### 11. Backend Hosting — Railway Pro

**What it does:**
Runs the FastAPI backend (`uvicorn app.main:app`), ARQ workers, and background services. Needs persistent WebSocket support (critical for voice calls), always-on (no cold starts), enough RAM for concurrent pipelines.

**Why Railway over Render:**
Usage-based billing, better WebSocket handling, faster deploys, no cold starts on Pro. Render's free tier sleeps after 15 minutes — completely unusable for live calls.

**Plans:**

| Plan | Monthly | Included Usage | Best For |
|---|---|---|---|
| Hobby | $5 | $5 of compute | Dev only |
| **Pro** | **$20/seat** | **$20 of compute** | **Production** |

Resource pricing on Pro:
- Memory: $0.00000386/GB-second
- CPU: $0.000463/vCPU-second

A FastAPI backend with ARQ workers (~512MB RAM, 0.5 vCPU always-on): **~$15–25/mo total** (Pro plan covers most of it).

**Recommended plan:** **Railway Pro ($20/mo).** Deploy 2 services: `api` (FastAPI) + `worker` (ARQ). Total: **~$40/mo** for both services.

---

### 12. Frontend Hosting — Vercel Pro

**What it does:**
Serves the Next.js 15 frontend (dashboard, agents, billing, calls pages). Global CDN, automatic deployments on push.

**Plans:**

| Plan | Monthly | Bandwidth | Best For |
|---|---|---|---|
| Hobby | $0 | 100 GB | Personal only (no commercial use) |
| **Pro** | **$20/seat** | **1 TB included** | **Production / commercial** |

> ⚠️ **Important:** Vercel's free Hobby plan explicitly prohibits commercial use. Auris is a commercial product — you must be on Pro.

**Recommended plan:** **Vercel Pro ($20/mo).** Covers Next.js frontend completely at early scale.

---

## COMPLETE SUMMARISED TABLE

| # | Service | Role in Auris | Recommended Plan | Monthly Cost | One-Time Setup |
|---|---|---|---|---|---|
| 1 | **Deepgram** | English STT (streaming WebSocket) | Growth ($4K/yr) | **$333/mo** | Free account |
| 2 | **Sarvam AI** | Indian STT + TTS (Hindi/Telugu/Tamil) | Pro → Business | **~₹2,000–5,000/mo + usage** | Free signup |
| 3 | **OpenAI** | LLM standard/premium + customer memory | PAYG (Tier 2) | **$3–50/mo (usage)** | Add card, spend $50 |
| 4 | **Groq** | LLM economy tier (Llama 4) | PAYG | **~$1–5/mo (usage)** | Free signup |
| 5 | **ElevenLabs** | English TTS (voice synthesis) | Creator → Pro | **$22–99/mo** | Free signup |
| 6 | **Telnyx** | Phone calls (SIP + WebSocket) | PAYG + DID numbers | **$50–200/mo (usage)** | Fund balance |
| 7 | **Razorpay** | Customer billing (INR credits) | Standard (PAYG) | **2% per txn** | KYC (1–3 days) |
| 8 | **Neon** | PostgreSQL + pgvector database | Launch | **~$20–25/mo** | Free signup |
| 9 | **Upstash** | Redis (ARQ jobs + rate limits) | PAYG / Fixed $10 | **$2–10/mo** | Free signup |
| 10 | **Cloudflare R2** | Audio/file storage (S3-compatible) | PAYG | **~$1–5/mo** | Free signup |
| 11 | **Railway** | FastAPI backend + ARQ workers | Pro | **~$40/mo** | Free signup |
| 12 | **Vercel** | Next.js frontend | Pro | **$20/mo** | Free signup |

---

## TOTAL MONTHLY COST SUMMARY

### Phase 1 — Launch / Early Production (0–100 call-hours/month)

| Category | Cost |
|---|---|
| AI — Deepgram (PAYG, within $200 free credits) | $0 |
| AI — Sarvam (low usage, within free tier) | ₹100–500 |
| AI — OpenAI (PAYG) | ~$1 |
| AI — Groq (PAYG) | ~$0 |
| AI — ElevenLabs Creator | $22 |
| AI — Telnyx (low call volume) | ~$20 |
| Infra — Neon Launch | $20 |
| Infra — Upstash PAYG | ~$2 |
| Infra — Cloudflare R2 | ~$1 |
| Infra — Railway Pro (2 services) | $40 |
| Infra — Vercel Pro | $20 |
| **TOTAL (launch phase)** | **~$130/mo + ₹500** |

---

### Phase 2 — Growing (500 call-hours/month)

| Category | Cost |
|---|---|
| AI — Deepgram (Growth plan) | $333 |
| AI — Sarvam (production usage) | ₹60,000 (~$720) |
| AI — OpenAI (Tier 2, GPT-4o-mini) | ~$20 |
| AI — Groq (PAYG) | ~$3 |
| AI — ElevenLabs Pro | $99 |
| AI — Telnyx (500 hrs × 60 min × $0.0055) | $165 |
| Infra — Neon Launch | $25 |
| Infra — Upstash Fixed | $10 |
| Infra — Cloudflare R2 | $5 |
| Infra — Railway Pro | $40 |
| Infra — Vercel Pro | $20 |
| **TOTAL (500 hrs/mo)** | **~$720 USD + ~₹60,000** |
| **≈ Total in INR** | **~₹1.2 lakh/mo** |

---

### Revenue vs. Cost at Scale

| Charging Rate | 500 hrs/mo Revenue | Total Cost | Profit | Margin |
|---|---|---|---|---|
| ₹5–6/min | ₹1,65,000 | ~₹1,20,000 | ~₹45,000 | **~27%** |
| ₹8–10/min | ₹2,40,000–3,00,000 | ~₹1,20,000 | ~₹1,20,000–1,80,000 | **~50–60%** |

---

### The 3 Things to Set Up Immediately (in order)

1. **Razorpay KYC** — takes 1–3 days, blocks going live. Start this first.
2. **Neon + Upstash + Cloudflare R2** — 30 minutes total, all free tiers, replace the local docker-compose infrastructure.
3. **Deepgram + Sarvam + OpenAI + ElevenLabs + Telnyx** — get free-tier API keys, test on PAYG, upgrade to paid plans as call volume grows.

---

### AI Provider Cost Per Minute — Quick Reference

| Tier | STT | LLM | TTS | Telephony | Total/min | Suggested Auris Price |
|---|---|---|---|---|---|---|
| Economy (English) | Deepgram $0.0043 | Groq ~$0.0001 | ElevenLabs $0.025 | Telnyx $0.0055 | **~$0.035/min** | ₹5–6/min |
| Standard (English) | Deepgram $0.0043 | GPT-4o-mini ~$0.0001 | ElevenLabs $0.025 | Telnyx $0.0055 | **~$0.035/min** | ₹6–8/min |
| Premium (English) | Deepgram $0.0043 | GPT-4o ~$0.0015 | ElevenLabs $0.025 | Telnyx $0.0055 | **~$0.037/min** | ₹10–12/min |
| Hindi/Indian | Sarvam $0.006 | GPT-4o-mini ~$0.0001 | Sarvam $0.018 | Telnyx $0.0055 | **~$0.030/min** | ₹5–6/min |

> **Key insight:** TTS (ElevenLabs) is 70–80% of your total API cost per call. Optimising agent response length has more impact on margin than any LLM model switch.
