<div align="center">

# 👑 AURIS VOICE AI PLATFORM

**Turnkey, Enterprise-Grade Conversational Voice AI SaaS Platform**  
*Build, deploy, and scale ultra-low latency voice agents over Telephony & WebRTC — with 100% codebase & IP ownership.*

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL pgvector](https://img.shields.io/badge/Vector_DB-pgvector-336791.svg?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Pytest Verified](https://img.shields.io/badge/Verification-100%25_Pass-brightgreen.svg)]()

[Features](#-core-platform-capabilities) • [Comparison vs Vapi/Retell](#-why-auris-vs-retell-ai--vapi) • [Architecture](#-system-architecture) • [Quickstart](#-quickstart-guide) • [Commercial Launch](#-commercial-roadmap--gtm)

</div>

---

## ⚡ Overview

**Auris** is an enterprise-grade Conversational Voice AI platform architected from scratch. Unlike proprietary vendor APIs (Retell AI, Vapi, Bland AI) where founders pay high per-minute markups and forfeit speech data ownership, Auris gives businesses **complete structural independence**:

1. **Wholesale Pass-Through Economics**: Connect your raw carrier and LLM vendor keys. Pay direct wholesale rates (`~$0.01 – $0.03/min`) with zero platform tax.
2. **Sub-Second Latency Pipeline**: Custom async frame engine (`STT → LLM → TTS`) featuring natural turn-taking, intelligent interruption handling (barge-in), and multi-lingual voice synthesis.
3. **Turnkey SaaS Commercialization**: Built-in multi-tenant organization boundaries, Razorpay pre-paid credit billing (`₹1 = 1 credit`), signed webhooks, Langfuse tracing, and exportable analytics.

---

## 🌟 Core Platform Capabilities

* 🎙️ **Custom Real-Time Voice Engine**: Asynchronous streaming pipeline buffers providing ultra-low speech latency (< 600ms) over WebSocket and WebRTC.
* 🎨 **Visual Workflow Graph Studio**: Interactive drag-and-drop workspace powered by `@xyflow/react` (React Flow 12). Design multi-branch agent flows with custom visual nodes (`agent`, `startCall`, `endCall`, `webhook`, `qa`, `tuner`), edge routers, and strict cycle detection.
* 📞 **Carrier-Agnostic Telephony**: SIP trunking, Asterisk ARI manager, Telnyx / Twilio webhooks, and instant DID phone number provisioning REST routes (`/telephony/phone-numbers`).
* 📚 **pgvector Knowledge Base RAG**: Automated document ingestion (`POST /knowledge-base/upload-url`) for PDF/TXT/DOCX files up to 100MB, 1536-dimensional embedding storage, and live semantic chunk retrieval during conversations.
* 🚀 **Parallel Outbound Dialer Campaigns**: CSV contact upload manager (`POST /campaign/upload`), asynchronous `ARQ` background workers (`dialer_worker`), and Redis token-bucket rate limiting.
* 🧠 **Repeat Caller Customer Memory**: Automated returning customer phone number identification and dynamic prompt injection of prior call summaries.
* 🛡️ **Native MCP Server & SDKs**: Built-in Model Context Protocol server mounted at `/api/v1/mcp` and auto-generated OpenAPI client SDKs.

---

## 👑 Why Auris vs. Retell AI & Vapi?

| Feature | Retell AI / Vapi | 🟢 Auris Enterprise Platform |
| :--- | :--- | :--- |
| **Codebase & Data Ownership** | Closed-Source SaaS | **100% Open & Owned**: Deploy in your own AWS/GCP VPC. Zero vendor lock-in. |
| **Wholesale Cost per Minute** | $0.08 – $0.30+ / min | **$0.01 – $0.03 / min**: Direct pass-through API costs. **Save 80%+ on operating margins.** |
| **Visual Workflow Builder** | Closed canvas studio | **React Flow 12 Studio**: Fully extensible React custom nodes & dagre auto-layouting. |
| **Carrier Telephony Flexibility** | Tied to vendor SIP trunks | **Bring Your Own Carrier**: Connect Telnyx, Twilio, Vonage, or custom SIP PBX. |
| **Hybrid Document RAG** | Basic document search | **pgvector RAG Engine**: Dedicated background chunking workers & semantic injection. |
| **Observability & SLAs** | Vendor dashboard only | **Langfuse & Sentry**: Cross-worker real-time LLM cost tracking & crash reporting. |

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph "External Channels"
        TEL[SIP / Telephony Carriers <br/> Telnyx / Twilio / ARI]
        WEB[WebRTC Browser Client <br/> Next.js Studio]
    end

    subgraph "Auris Backend Core [FastAPI]"
        WS[Consolidated Telephony WebSocket Route]
        PIPE[Custom Frame Pipeline Engine <br/> STT Nova-2 ──► LLM GPT-4o ──► TTS Cartesia]
        WORKER[ARQ Background Workers <br/> Dialer Campaigns & RAG Embeddings]
    end

    subgraph "Data & Storage Layer"
        PG[(PostgreSQL + pgvector <br/> Tenants / Workflows / Embeddings)]
        REDIS[(Redis Cluster <br/> ARQ Jobs / Rate Limits)]
        S3[(MinIO / S3 Storage <br/> Audio Recordings / CSVs)]
    end

    TEL <──► WS
    WEB <──► WS
    WS <──► PIPE
    PIPE <──► WORKER
    PIPE <──► PG
    WORKER <──► REDIS
    WORKER <──► S3
```

---

## 🌐 Supported Language & AI Vendors

| Language | Recommended STT | Recommended LLM | Recommended TTS |
| :--- | :--- | :--- | :--- |
| **English** | Deepgram Nova-2 | OpenAI GPT-4o / Groq Llama 3 | Cartesia / ElevenLabs |
| **Hindi** | Deepgram / Sarvam | OpenAI GPT-4o / Groq | Cartesia / Sarvam Bulbul |
| **Telugu / Tamil** | Sarvam AI | OpenAI GPT-4o | Sarvam Bulbul |

---

## 🚀 Quickstart Guide

### 1. Clone & Configure Credentials
```bash
git clone https://github.com/venkat-karthik/auris.git
cd auris
cp backend/.env.example backend/.env
# Add your vendor keys (OPENAI_API_KEY, DEEPGRAM_API_KEY, RAZORPAY_KEY_ID, etc.)
```

### 2. Launch Container Stack (Postgres + pgvector, Redis, MinIO)
```bash
docker compose up postgres redis minio -d
```

### 3. Initialize Database Tables
```bash
cd backend
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
```

### 4. Start API Server
```bash
# Backend Server (Port 8000)
uvicorn app.main:app --reload --port 8000
```

* 📖 **OpenAPI Swagger Docs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

## 🗺️ Commercial Roadmap & Status

- [x] **Milestone 1 — Outbound Dialer Campaigns**: CSV contact upload manager (`POST /campaign/upload`), ARQ background workers, and Redis rate limiting.
- [x] **Milestone 2 — pgvector Knowledge Base RAG**: S3/MinIO ingestion up to 100MB, vector embedding storage, and live conversation injection.
- [x] **Milestone 3 — Visual Workflow Builder**: React Flow 12 studio canvas at `/workflow/[id]` with graph validation and execution engine.
- [x] **Milestone 4 — Telemetry & Visualizations**: Animated speech audio waveforms and consolidated telephony streaming routes.
- [x] **Milestone 5 — Multi-Tenant SaaS Commercialization**: Razorpay self-serve credit top-ups, daily analytics reports, and full test suite verification (**100% pass across 997 pytest unit tests**).

---

## 📄 License & Ownership

Auris is open-source software released under the **MIT License**.  
**100% Owned by Venkat Karthik & Zovance.**
