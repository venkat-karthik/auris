# 📊 Auris: Commercial Pricing & Deployment Guide

This guide details the cost calculations, SaaS pricing plans, and deployment procedures required to commercialize Auris as a premium Voice AI platform (similar to Retell or Vapi).

---

## 1. 💰 Underlying API Provider Costs

Below are the direct utility prices charged by the integrated STT, LLM, TTS, and Telephony providers.

### A. Speech-To-Text (STT)
| Provider | Model / Language | Cost per Minute |
| :--- | :--- | :--- |
| **Deepgram** | Nova-2 (English / Global) | **$0.0043 / min** |
| **Sarvam AI** | Vernacular STT (Hindi, Telugu, etc.) | **$0.0012 / min** (₹0.10 INR) |

### B. Large Language Model (LLM)
*Calculated based on an average conversation of 3 input-output turns per minute (approx. 1,200 tokens).*
| Provider | Model | Input (per 1M tokens) | Output (per 1M tokens) | Cost per Minute |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI** | GPT-4o-mini | $0.15 | $0.60 | **$0.0006 / min** |
| **OpenAI** | GPT-4o | $2.50 | $10.00 | **$0.0100 / min** |

### C. Text-To-Speech (TTS)
*Calculated based on an average speaker rate of 150 words (approx. 750 characters) per minute.*
| Provider | Voice Type | Rate per 1k Characters | Cost per Minute |
| :--- | :--- | :--- | :--- |
| **Sarvam AI** | Vernacular TTS (Indic Languages) | $0.0027 (₹0.22 INR) | **$0.0020 / min** |
| **ElevenLabs** | Multilingual v2 / Turbo (Premium) | $0.24 | **$0.0240 / min** |

### D. Telephony (Telnyx)
| Service | Rate / Unit |
| :--- | :--- |
| **Inbound Local Call Rate** | **$0.0035 / min** |
| **Outbound Local Call Rate** | **$0.0048 / min** |
| **Virtual Phone Number Lease** | **$1.00 / month** |

---

## 2. 🧮 Cost of Goods Sold (COGS) per Minute

We analyze two typical client conversational scenarios to establish our baseline cost per minute.

### Scenario A: Local Indian Vernacular Agent (Standard)
*Uses Sarvam STT + GPT-4o-mini + Sarvam TTS + Inbound Telephony.*
* **STT**: $0.0012
* **LLM**: $0.0006
* **TTS**: $0.0020
* **Telephony**: $0.0035
* **Total Cost / Minute**: **$0.0073 / minute** (approx. ₹0.60 INR)

### Scenario B: Ultra-Realistic English Agent (Premium)
*Uses Deepgram Nova-2 + GPT-4o + ElevenLabs Premium + Inbound Telephony.*
* **STT**: $0.0043
* **LLM**: $0.0100
* **TTS**: $0.0240
* **Telephony**: $0.0035
* **Total Cost / Minute**: **$0.0418 / minute** (approx. ₹3.50 INR)

---

## 3. 🎯 Proposed SaaS Pricing Plans

To achieve a strong 80%+ gross margin while remaining highly competitive with Retell ($0.08–$0.15/min) and Vapi ($0.15/min), we recommend the following subscription tiers:

```mermaid
graph TD
    A[Pricing Tiers] --> B[Basic Plan: $29/mo]
    A --> C[Medium Plan: $99/mo]
    A --> D[Premium Plan: $299/mo]
    
    B --> B1[500 Mins Included]
    B --> B2[COGS: $3.65 | Margin: 87%]
    
    C --> C1[2,000 Mins Included]
    C --> C2[COGS: $14.60 | Margin: 85%]
    
    D --> D1[7,000 Mins Included]
    D --> D2[COGS: $51.10 | Margin: 83%]
```

### 1. Basic Plan (Starter)
*Ideal for small offices or single-agent receptionists.*
* **Monthly Price**: **$29 / month** (₹2,400 INR)
* **Voice Minutes Included**: 500 mins / month (Standard Scenarios)
* **Phone Numbers**: 1 virtual line included ($1.00 value)
* **Markup Calculations**:
  * **Our Minute Cost (COGS)**: 500 * $0.0073 + $1.00 = **$4.65**
  * **Gross Profit Margin**: **84%** ($24.35 profit)
  * **Overage Billing**: **$0.08 / minute** (₹6.50 INR)

### 2. Medium Plan (Growth)
*Ideal for scaling storefronts and outbound list campaigns.*
* **Monthly Price**: **$99 / month** (₹8,200 INR)
* **Voice Minutes Included**: 2,000 mins / month
* **Phone Numbers**: 2 virtual lines included ($2.00 value)
* **Markup Calculations**:
  * **Our Minute Cost (COGS)**: 2,000 * $0.0073 + $2.00 = **$16.60**
  * **Gross Profit Margin**: **83%** ($82.40 profit)
  * **Overage Billing**: **$0.06 / minute** (₹5.00 INR)

### 3. Premium Plan (Enterprise)
*Ideal for call centers, high-volume campaigns, and ElevenLabs premium voice integrations.*
* **Monthly Price**: **$299 / month** (₹24,800 INR)
* **Voice Minutes Included**: 7,000 mins / month (Includes ElevenLabs hours)
* **Phone Numbers**: 5 virtual lines included ($5.00 value)
* **Markup Calculations**:
  * **Our Minute Cost (COGS)**: 7,000 * $0.0073 + $5.00 = **$56.10**
  * **Gross Profit Margin**: **81%** ($242.90 profit)
  * **Overage Billing**: **$0.05 / minute** (₹4.00 INR)

---

## 4. 🚀 Step-by-Step Cloud Deployment

Follow these instructions to host Auris in a secure production environment.

### 1. Database Provisioning
1. Spin up a PostgreSQL instance on **Supabase** or **AWS RDS**.
2. Connect to the database and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Update `DATABASE_URL` in your env settings.

### 2. Redis Cache
1. Create a Redis connection URI using **Upstash Redis** or **Render Redis**.
2. Ensure you have the `REDIS_URL` populated to trigger the rate limiting middleware.

### 3. Backend Deployment (Render or AWS ECS)
Deploy the FastAPI backend container. Ensure the following environment parameters are set:
```env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://user:pass@host:port
STORAGE_BACKEND=s3
MINIO_ENDPOINT=s3.amazonaws.com
MINIO_ACCESS_KEY=your-aws-access-key
MINIO_SECRET_KEY=your-aws-secret-key
MINIO_BUCKET=auris-voice-records
```
Ensure you run **two distinct worker tasks**:
* Web server task: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
* Campaign worker task: `arq app.services.campaign_dialer.WorkerSettings`

### 4. Next.js Frontend Deployment (Vercel)
Deploy your Next.js application to Vercel. Bind this key variable:
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

### 5. Telephony Connection
Point your Telnyx connection webhook to:
`https://api.yourdomain.com/api/v1/telephony/inbound`
