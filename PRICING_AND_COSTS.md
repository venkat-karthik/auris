# 💰 AURIS PRICING & COST STRUCTURE GUIDE

**Version:** 1.0.0  
**Last Updated:** July 2026  
**Currency:** Indian Rupees (₹) / US Dollars ($)

---

## 📑 Table of Contents

1. [Credit System Overview](#credit-system-overview)
2. [Wholesale Cost Breakdown](#wholesale-cost-breakdown)
3. [Platform Pricing Models](#platform-pricing-models)
4. [Cost Calculation Examples](#cost-calculation-examples)
5. [Billing & Payment Process](#billing--payment-process)
6. [Cost Optimization Strategies](#cost-optimization-strategies)
7. [Competitive Comparison](#competitive-comparison)
8. [Enterprise Pricing](#enterprise-pricing)

---

## 🎯 Credit System Overview

### What is a Credit?

**1 Credit = ₹1.00 (Indian Rupee)**

Every action in Auris is charged in credits:
- **Call Minutes**: Pay per minute of speech
- **Knowledge Base**: One-time ingestion charge
- **Campaigns**: Charged per call attempt
- **SMS/WhatsApp**: Additional channels (coming soon)

### Credit Purchase Options

| Amount (₹) | Credits | Usage Example |
|-----------|---------|---------------|
| ₹100 | 100 | ~8-10 calls (5 min avg) |
| ₹500 | 500 | ~40-50 calls (5 min avg) |
| ₹1,000 | 1,000 | ~80-100 calls (5 min avg) |
| ₹2,500 | 2,500 | ~200-250 calls (5 min avg) |
| ₹4,999 | 4,999 | ~400-500 calls (5 min avg) |

### Minimum & Maximum Limits

- **Minimum Purchase**: ₹100 (100 credits)
- **Maximum Single Transaction**: ₹4,999 (4,999 credits)
- **No Expiration**: Credits remain valid indefinitely
- **Refund Policy**: No refunds on prepaid credits (non-refundable)
- **Transfer**: Credits are organization-specific, not transferable

### Currency Conversion

| INR | USD (Approximate) | EUR (Approximate) |
|-----|-------------------|------------------|
| ₹100 | $1.20 | €1.10 |
| ₹500 | $6.00 | €5.50 |
| ₹1,000 | $12.00 | €11.00 |
| ₹4,999 | $60.00 | €55.00 |

*Exchange rates subject to Razorpay current rates.*

---

## 🏷️ Wholesale Cost Breakdown

### Per-Minute Call Costs

Auris operates on **100% wholesale pass-through pricing** with **zero platform markup**.

#### Standard Configuration (GPT-4o + Deepgram + Cartesia)

| Component | Per-Minute Cost | Provider | Notes |
|-----------|-----------------|----------|-------|
| **STT** (Speech-to-Text) | $0.005 | Deepgram Nova-2 | Accurate, low-latency |
| **LLM** (Language Model) | $0.010 | OpenAI GPT-4o | Advanced reasoning |
| **TTS** (Text-to-Speech) | $0.005 | Cartesia | Natural-sounding voices |
| **Total Per Minute** | **$0.020** | | **₹1.65/min** |

#### Budget Configuration (Groq + Deepgram + Cartesia)

| Component | Per-Minute Cost | Provider | Notes |
|-----------|-----------------|----------|-------|
| **STT** (Speech-to-Text) | $0.005 | Deepgram Nova-2 | Standard |
| **LLM** (Language Model) | $0.003 | Groq Llama 3 | 3x cheaper |
| **TTS** (Text-to-Speech) | $0.005 | Cartesia | Standard |
| **Total Per Minute** | **$0.013** | | **₹1.07/min** |

#### Premium Configuration (GPT-4o Turbo + Deepgram + ElevenLabs)

| Component | Per-Minute Cost | Provider | Notes |
|-----------|-----------------|----------|-------|
| **STT** (Speech-to-Text) | $0.005 | Deepgram Nova-2 | Standard |
| **LLM** (Language Model) | $0.015 | OpenAI GPT-4o Turbo | Enhanced reasoning |
| **TTS** (Text-to-Speech) | $0.012 | ElevenLabs Pro | Premium voices |
| **Total Per Minute** | **$0.032** | | **₹2.64/min** |

### Carrier Costs (Phone Numbers)

#### Inbound Phone Numbers

| Carrier | Per-Month Cost | Per-Number | Features |
|---------|----------------|-----------|----------|
| **Telnyx** | $0.85 | +1, +44, +61 | SIP, WebRTC, SMS |
| **Twilio** | $1.00 | +1 (US/CA) | SIP, WebRTC, SMS |
| **Vonage** | $1.20 | Global | Premium support |

#### Outbound Calling Rates

| Carrier | Per-Minute Cost | Notes |
|---------|-----------------|-------|
| **Telnyx** | $0.005–0.015 | Variable by destination |
| **Twilio** | $0.010–0.020 | Variable by destination |
| **Custom SIP** | Varies | Customer-provided trunk |

**Note**: Auris only bills for speech service (STT+LLM+TTS), not carrier minutes.

---

---

## 📊 Platform Pricing Models

### Model 1: Pure Pay-As-You-Go (Current)

**No subscriptions. No minimums. No surprises.**

```
Total Cost = (Call Minutes × $/minute) + (Storage) + (Carrier)
```

**Example:**
- 100 calls × 5 minutes = 500 minutes
- 500 min × $0.020/min = $10 USD (~₹825)
- Phone number: $0.85/month (Telnyx)
- **Total**: ₹825 + ₹70 = **₹895/month**

### Model 2: Dedicated Team Plan (Coming v1.1)

**For organizations with ≥10 team members**

```
Base Fee: ₹5,000/month
+ Usage: ₹1.65 per call-minute
+ Phone Numbers: ₹70 each/month
```

### Model 3: Enterprise On-Premise (Custom Pricing)

**Deploy Auris in your own VPC**

- White-label voice AI platform
- Custom SLA guarantees
- Dedicated support engineer
- No usage-based charges (fixed monthly fee)
- **Contact sales**: enterprise@auris.xyz

---

## 📈 Cost Calculation Examples

### Scenario 1: Customer Support (Small Business)

**Setup:**
- 10 inbound support agents
- 1 phone number
- 50 calls/day
- 3-minute average duration

**Monthly Calculations:**
```
Calls per month: 50 × 30 = 1,500 calls
Duration: 1,500 × 3 min = 4,500 minutes
Speech cost: 4,500 min × $0.020/min = $90 USD (~₹7,425)
Phone number: 1 × ₹70 = ₹70
Carrier (outbound): ~₹500

TOTAL: ₹7,995/month
Cost per call: ₹5.33
```

**Credit Requirement:**
- Buy 2x ₹4,999 packages = ₹9,998 = ~8,000 calls at 5 min avg
- Sufficient for ~2 months

---

### Scenario 2: Outbound Sales Campaigns (Medium Enterprise)

**Setup:**
- 3 sales agents
- 5 phone numbers (different area codes)
- 10,000 contacts/month
- 2-minute average call duration
- 60% answer rate = 6,000 actual calls

**Monthly Calculations:**
```
Answered calls: 6,000
Duration: 6,000 × 2 min = 12,000 minutes
Speech cost: 12,000 min × $0.020/min = $240 USD (~₹19,800)
Phone numbers: 5 × ₹70 = ₹350
Carrier (outbound): ~₹2,000

TOTAL: ₹22,150/month (~$267 USD)
Cost per successful call: ₹3.68
```

**Credit Requirement:**
- Buy 5x ₹4,999 packages = ₹24,995 = ~400 calls/package
- Sufficient for ~1.5 months

---

### Scenario 3: Knowledge Base RAG (Enterprise)

**Setup:**
- 50 PDF documents ingested
- 100 calls/day with semantic search
- 4-minute average duration
- Cartesia TTS upgraded to ElevenLabs

**Monthly Calculations:**
```
Calls per month: 100 × 30 = 3,000 calls
Duration: 3,000 × 4 min = 12,000 minutes
Speech cost: 12,000 min × $0.032/min = $384 USD (~₹31,680)
  (GPT-4o Turbo + ElevenLabs)
Document ingestion: One-time ~₹500
Phone numbers: 2 × ₹70 = ₹140
Carrier: ~₹1,000

TOTAL: ₹33,320/month
Cost per call: ₹11.10
```

**Credit Requirement:**
- Buy 7x ₹4,999 packages = ₹34,993
- Sufficient for ~1 month

---

### Scenario 4: 24/7 Multilingual Support Bot

**Setup:**
- 1 AI agent (serves all languages)
- 200 inbound calls/day
- 5-minute average duration
- Sarvam AI STT/TTS for Hindi

**Monthly Calculations:**
```
Calls per month: 200 × 30 = 6,000 calls
Duration: 6,000 × 5 min = 30,000 minutes

Cost breakdown:
- Deepgram (English STT): $0.005/min
- OpenAI GPT-4o (any language): $0.010/min
- Sarvam TTS (Indian languages): $0.008/min
- Total: $0.023/min (~₹1.90/min)

Total: 30,000 × $0.023 = $690 USD (~₹56,970)
Phone number: ₹70
Carrier: ~₹2,000

TOTAL: ₹59,040/month
Cost per call: ₹9.84
```

**Credit Requirement:**
- Buy 12x ₹4,999 packages = ₹59,988
- Sufficient for ~1 month

---

## 💳 Billing & Payment Process

### Step 1: Create Razorpay Order

```bash
POST /api/v1/billing/razorpay/create-order
{
  "amount_inr": 2500
}
```

**Response:**
```json
{
  "order_id": "order_9A33XWu590gUtm",
  "amount_paise": 250000,
  "currency": "INR",
  "key_id": "rzp_test_xxxxxxxx"
}
```

### Step 2: Complete Payment

Frontend integrates Razorpay checkout:
```javascript
var options = {
    "key": "rzp_test_xxxxxxxx",
    "amount": 250000,
    "currency": "INR",
    "name": "Auris",
    "order_id": "order_9A33XWu590gUtm",
    "handler": function (response){
        // Send to backend for verification
        verifyPayment(response);
    }
};
var rzp1 = new Razorpay(options);
rzp1.open();
```

### Step 3: Verify Payment Signature

```bash
POST /api/v1/billing/razorpay/verify-payment
{
  "razorpay_order_id": "order_9A33XWu590gUtm",
  "razorpay_payment_id": "pay_9A33XWu590gUtm",
  "razorpay_signature": "9ef4dffbfd84f1318f6739a3ce19f9d85851857ae648f114332d8401e0949a"
}
```

**Response:**
```json
{
  "success": true,
  "credits_added": 2500.0,
  "new_balance": 3725.0
}
```

### Step 4: Check Balance

```bash
GET /api/v1/billing/balance
```

**Response:**
```json
{
  "balance_credits": 3725.0,
  "transactions": [
    {
      "razorpay_order_id": "order_9A33XWu590gUtm",
      "amount_paise": 250000,
      "credits_added": 2500.0,
      "status": "completed",
      "created_at": "2026-07-21T10:30:00Z",
      "completed_at": "2026-07-21T10:31:00Z"
    }
  ]
}
```

### Payment Security

- **PCI Compliant**: Razorpay handles all payment processing
- **No Card Storage**: Cards never stored in Auris database
- **Webhook Verification**: HMAC-SHA256 signature verification
- **Idempotency**: Duplicate payments prevented via razorpay_order_id

---

## ⚙️ Cost Optimization Strategies

### Strategy 1: Use Groq Instead of OpenAI

**Impact**: ~70% LLM cost reduction

```
Current: GPT-4o @ $0.010/min
Groq:    Llama 3 @ $0.003/min
Savings: $0.007/min per call

Example: 5,000 calls/month × 3 min avg
= 15,000 minutes
= 15,000 × $0.007 = $105 saved/month (~₹8,650)
```

### Strategy 2: Optimize Prompt Length

**Impact**: ~20% token reduction

Shorter system prompts = fewer tokens = cheaper LLM costs.

```
❌ Long prompt (2KB): 200 tokens
✅ Short prompt (500B): 80 tokens

Savings: 120 tokens × $0.0001 per token = $0.012/call
× 5,000 calls = $60/month (~₹4,950)
```

### Strategy 3: Batch Campaigns in Off-Peak Hours

**Impact**: Potential 10% carrier discount

Many carriers offer lower rates during off-peak:
- 10 PM – 6 AM (local time)
- Weekends

### Strategy 4: Reuse Knowledge Base Embeddings

**Impact**: No re-ingestion charges

- Upload document once
- Use across multiple agents
- Embeddings cached in pgvector
- Save: ~₹500 per re-upload

### Strategy 5: Monitor & Alert on Budget Overspend

```python
# Programmatic budget monitoring
current_balance = auris_client.get_balance()
if current_balance < 100:
    # Trigger alert: "Running low on credits"
    send_slack_alert("Balance below ₹100")
    
# Estimate monthly spend
estimated_monthly = agent_analytics["total_cost"] * 30
if estimated_monthly > monthly_budget:
    # Cap calls or pause campaigns
    campaigns_to_pause = identify_low_roi_campaigns()
```

### Strategy 6: Leverage Free Tier (Development)

- **Development**: Use mock API keys
- **Testing**: Make test calls without charging
- **Setup**: Zero-cost configuration phase

---

---

## 🏆 Competitive Comparison

### Auris vs. Retell AI vs. Vapi vs. Bland AI

| Factor | Auris | Retell AI | Vapi | Bland AI |
|--------|-------|-----------|------|----------|
| **Cost/Minute** | $0.020 | $0.12 | $0.10 | $0.15 |
| **Margin Improvement** | 0% markup | 500%+ markup | 400%+ markup | 650%+ markup |
| **Ownership** | 100% yours | Vendor owned | Vendor owned | Vendor owned |
| **Min. Purchase** | ₹100 | $10 | $10 | $10 |
| **Setup Time** | 5 min | 30 min | 30 min | 30 min |
| **Custom Workflows** | React Flow 12 | Limited | Limited | Very Limited |
| **Carrier Choice** | Unlimited | Telnyx only | Telnyx only | Limited |
| **RAG Capability** | pgvector | Basic | Basic | None |
| **Deployment** | Your VPC | SaaS only | SaaS only | SaaS only |
| **Data Privacy** | You control | Shared servers | Shared servers | Shared servers |

### Cost Example: 10,000 Calls/Month (5 min avg)

**Call Volume**: 50,000 total minutes

| Platform | Cost | Monthly Spend | Savings vs Auris |
|----------|------|---------------|------------------|
| **Auris** | $0.020/min | **$1,000** | **Baseline** |
| **Retell** | $0.120/min | $6,000 | +500% |
| **Vapi** | $0.100/min | $5,000 | +400% |
| **Bland** | $0.150/min | $7,500 | +650% |

**Annual Savings with Auris**: $60,000 – $78,000 vs competitors

---

## 🏢 Enterprise Pricing

### Enterprise On-Premise Deployment

**For Organizations Needing:**
- 100,000+ calls/month
- Custom SLA guarantees
- Dedicated support engineer
- White-label platform

#### Pricing Tiers

| Tier | Monthly Fee | Included Calls | Support |
|------|------------|-----------------|---------|
| **Enterprise Starter** | $5,000 | 250,000 calls | Email |
| **Enterprise Pro** | $15,000 | 1,000,000 calls | 24/7 Phone |
| **Enterprise Max** | $30,000 | 5,000,000 calls | Dedicated Engineer |

**Per-Call Overage**: $0.001/call beyond included volume

### Enterprise Benefits

✅ **Fixed Monthly Cost** (no per-minute surprises)  
✅ **Dedicated Kubernetes Cluster** (your own infrastructure)  
✅ **White-Label Branding** (remove Auris logos)  
✅ **Advanced Integrations** (Salesforce, HubSpot, custom APIs)  
✅ **Priority Support** (4-hour response SLA)  
✅ **Custom Features** (workflow extensions, special routing)  
✅ **Uptime SLA** (99.99% guaranteed)  

### Enterprise Implementation

1. **Initial Consultation**: Understand requirements (1-2 weeks)
2. **Infrastructure Setup**: Deploy in customer VPC (1-2 weeks)
3. **Integration**: Connect to customer systems (2-4 weeks)
4. **Training**: Onboard customer team (1 week)
5. **Go-Live**: Production deployment (1-2 weeks)

**Total Timeline**: 6-10 weeks from contract to production

### Enterprise Support SLAs

| Severity | Response Time | Resolution Time |
|----------|---------------|-----------------|
| **Critical** (Down) | 30 min | 4 hours |
| **High** (Degraded) | 2 hours | 24 hours |
| **Medium** (Issues) | 4 hours | 48 hours |
| **Low** (Questions) | 24 hours | 5 days |

---

## 💡 Cost Control Features

### Hard Limits (Coming v1.1)

Prevent accidental overspend:

```bash
# Set monthly budget cap
PUT /api/v1/organizations/{org_id}/settings
{
  "monthly_budget_credits": 10000,
  "auto_pause_campaigns": true,
  "budget_alert_threshold": 80  # Alert at 80% spent
}
```

### Usage Quotas

```bash
# Limit agents to X calls/month
PUT /api/v1/agents/{agent_id}/quota
{
  "max_calls_per_month": 1000,
  "max_cost_per_month": "2000"  # ₹2000
}
```

### Auto-Pause on Budget

```bash
# Automatically pause campaigns when budget reached
PUT /api/v1/organizations/{org_id}/settings
{
  "auto_pause_on_budget_exceeded": true
}
```

---

## 📊 Cost Reporting & Analytics

### Monthly Cost Report

```bash
GET /api/v1/analytics/cost-report?month=2026-07
```

**Response:**
```json
{
  "period": "2026-07",
  "total_cost_usd": 250.00,
  "total_cost_inr": 20625.00,
  "by_agent": [
    {
      "agent_id": 1,
      "agent_name": "Sales Bot",
      "calls": 150,
      "minutes": 450,
      "cost_usd": 9.00,
      "cost_inr": 741.00
    }
  ],
  "by_service": {
    "speech_services": 250.00,
    "phone_numbers": 5.00,
    "carrier": 0.00
  },
  "credits_used": 20625,
  "credits_purchased": 25000,
  "credits_remaining": 4375
}
```

### Per-Agent Cost Breakdown

```bash
GET /api/v1/analytics/agents
```

Shows each agent's:
- Total calls made
- Total minutes used
- Average call duration
- Total cost (USD + INR)
- Cost per call
- Conversion rate (for ROI calculation)

### Campaign ROI Analysis

```bash
GET /api/v1/campaigns/{campaign_id}/roi
```

**Response:**
```json
{
  "campaign_id": 1,
  "total_calls": 1000,
  "successful_calls": 250,
  "success_rate": 25.0,
  "total_cost_usd": 100.00,
  "cost_per_successful_call": 0.40,
  "estimated_revenue": 2500.00,
  "roi": "2,500%"
}
```

---

## ⚠️ Hidden Costs to Watch

### ❌ What You DON'T Pay (Unlike Competitors)

- **No Platform Tax**: $0 markup on speech services
- **No Setup Fee**: Free account creation
- **No API Call Tax**: Unlimited API calls (read/write)
- **No Seat Licenses**: Unlimited team members
- **No Data Export Fee**: Export data anytime
- **No Hidden Minimums**: Stop anytime

### ⚠️ What You SHOULD Budget For

1. **Phone Numbers** (~₹70/number/month)
   - Used for inbound/outbound calling
   - Required even for WebRTC

2. **Carrier Minutes** (varies)
   - Additional charge from Telnyx/Twilio
   - Not included in Auris per-minute cost
   - Example: Telnyx $0.005–0.015/min outbound

3. **Storage** (if using custom videos/documents)
   - MinIO storage: ₹500/100GB/month
   - Recordings auto-deleted after 90 days
   - No charge for call recordings (included)

4. **Custom Integrations** (if needed)
   - Salesforce CRM sync: Custom development
   - Legacy PBX integration: Custom work
   - Estimate: $2,000–5,000 per integration

---

## 🎁 Free Tier & Trials

### Development Free Tier

**Unlimited free usage for:**
- ✅ Development/Testing (mock API keys)
- ✅ Agent creation & management
- ✅ Knowledge base uploads (no embedding charges)
- ✅ Workflow design (no execution)

### Production Trial

**14-day free production trial:**
- ✅ 500 call minutes (any carrier)
- ✅ 2 phone numbers included
- ✅ Full feature access
- ✅ Full support

**After trial:**
- Upgrade to credit plan
- No auto-billing (you control charges)

---

## 📞 Billing Support

**Questions About Costs?**
- Email: billing@auris.xyz
- Docs: https://docs.auris.xyz/pricing
- Calculator: https://auris.xyz/pricing-calculator

**Bulk Discount Negotiations:**
- Contact: enterprise@auris.xyz
- Minimum: $1,000/month spend
- Potential savings: 15–30%

---

## 🔐 Invoice & Tax

### Invoice Format

```
INVOICE #: INV-2026-07-001

Bill To: Organization Name
Email: admin@company.com

Description: Auris Voice AI Platform - July 2026
Period: 2026-07-01 to 2026-07-31

Subtotal: ₹20,625.00
Tax (18% GST): ₹3,712.50
Total Due: ₹24,337.50

Payment Method: Razorpay
Payment Date: 2026-07-21
Status: PAID ✓
```

### Tax Compliance

- **GST**: 18% applied in India (registered businesses can claim credit)
- **Invoice**: Auto-generated for each transaction
- **Download**: Available in billing dashboard
- **Export**: CSV/PDF formats supported

---

**Last Updated**: July 21, 2026  
**Maintained By**: Venkat Karthik & Zovance  
**Version**: 1.0.0
