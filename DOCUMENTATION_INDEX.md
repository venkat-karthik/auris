# 📚 AURIS DOCUMENTATION INDEX

**Complete Auris Platform Documentation Suite**  
Last Updated: July 21, 2026

---

## 🎯 Quick Navigation

### For First-Time Users
1. Start here → **[README.md](./README.md)** - Platform overview & key differentiators
2. Then → **[STARTUP.md](./STARTUP.md)** - Local setup & deployment
3. Next → **[WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md)** - Core concepts

### For Developers Integrating APIs
1. **[WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md)** - Complete API reference
   - Authentication endpoints
   - Agent management
   - Call operations
   - Knowledge base (RAG)
   - Campaigns & dialer
   - Billing & credits
   - Phone numbers & telephony

### For Business & Finance Teams
1. **[PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md)** - Complete cost breakdown
   - Credit system
   - Per-minute pricing
   - Cost calculations
   - Examples (all use cases)
   - ROI & budget planning

### For Operators & DevOps
1. **[STARTUP.md](./STARTUP.md)** - Deployment & configuration
2. **[WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md)** - Section: Integration Guide

---

## 📖 Document Overview

### 1. README.md (7.1 KB)
**What**: Platform introduction & features  
**Who**: Everyone (especially decision makers)  
**Contains:**
- Platform overview & value proposition
- Core capabilities
- Comparison vs. competitors
- System architecture diagram
- Commercial roadmap

**Best For**: Understanding "What is Auris?"

---

### 2. STARTUP.md (2.8 KB)
**What**: Local development & deployment setup  
**Who**: Developers & DevOps engineers  
**Contains:**
- Prerequisites & system requirements
- Step-by-step Docker setup
- Python environment configuration
- Database migrations
- First run verification

**Best For**: Getting Auris running locally in 5 minutes

---

### 3. WORKFLOW_DOCUMENTATION.md (42 KB) ⭐ MAIN REFERENCE
**What**: Complete platform workflow & API documentation  
**Who**: Developers, integrators, technical teams  
**Contains:**
- Quick start guide
- Complete workflow diagram
- Core architecture concepts
- All 50+ API endpoints with request/response examples
- 5 step-by-step workflows
- Integration guides
- Troubleshooting & FAQ (Q1-Q10)
- WebSocket/WebRTC details
- Carrier configuration (Telnyx, Twilio)
- AI vendor setup (OpenAI, Deepgram, Cartesia, Groq, Sarvam)

**Sections:**
```
1. Platform Overview
2. Quick Start Guide (5 min)
3. Complete Workflow Diagram
4. Core Concepts & Architecture
5. Pricing & Cost Structure
6. API Endpoints Reference (comprehensive)
7. Step-by-Step Workflows (5 real-world scenarios)
8. Integration Guide
9. Troubleshooting & FAQ
```

**Best For**: Understanding how everything works together

---

### 4. PRICING_AND_COSTS.md (18 KB)
**What**: Detailed pricing models & cost calculations  
**Who**: Finance teams, product managers, decision makers  
**Contains:**
- Credit system (₹1 = 1 credit)
- Wholesale cost breakdown by component
- 4 real-world cost calculation examples
- Billing process & payment flow
- Cost optimization strategies (6 techniques)
- Competitive comparison matrix
- Enterprise pricing tiers
- Cost control features
- ROI analysis examples
- Hidden costs to watch
- Free tier & trial information

**Cost Calculations Included:**
- Small business support (10 agents, 50 calls/day)
- Medium enterprise campaigns (10K contacts/month)
- Enterprise RAG (50 documents, 100 calls/day)
- 24/7 multilingual support (200 calls/day)

**Best For**: Budgeting & financial planning

---

## 🔑 Key Information Quick Reference

### Most Important URLs
```
API Base: http://localhost:8000
API Docs: http://localhost:8000/api/v1/docs (Swagger)
Health:   http://localhost:8000/api/v1/health
OpenAPI:  http://localhost:8000/api/v1/openapi.json
```

### Most Important Endpoints
```
Authentication:
  POST /api/v1/auth/signup
  POST /api/v1/auth/verify
  POST /api/v1/auth/login

Agents:
  POST /api/v1/agents (create)
  GET /api/v1/agents (list)
  PUT /api/v1/agents/{id} (update)

Calls:
  POST /api/v1/calls/dispatch (outbound)
  GET /api/v1/calls (list)
  GET /api/v1/calls/{id}/transcript

Billing:
  POST /api/v1/billing/razorpay/create-order
  POST /api/v1/billing/razorpay/verify-payment
  GET /api/v1/billing/balance

Knowledge Base:
  POST /api/v1/knowledge-base/upload
  GET /api/v1/knowledge-base

Campaigns:
  POST /api/v1/campaigns (create)
  POST /api/v1/campaigns/{id}/contacts/upload
  POST /api/v1/campaigns/{id}/start
```

### Most Important Costs
```
Speech per minute: $0.020 USD (~₹1.65)
  - STT (Deepgram):  $0.005
  - LLM (GPT-4o):    $0.010
  - TTS (Cartesia):  $0.005

Phone number: ₹70/month (Telnyx)
Minimum purchase: ₹100 credits
Maximum purchase: ₹4,999 credits
```

### Most Important Configuration
```
Environment Variables (backend/.env):
- OPENAI_API_KEY
- DEEPGRAM_API_KEY
- TELNYX_API_KEY or TWILIO_ACCOUNT_SID
- RAZORPAY_KEY_ID + RAZORPAY_KEY_SECRET
- DATABASE_URL (PostgreSQL + pgvector)
- REDIS_URL
- MINIO_ENDPOINT (MinIO object storage)
```

---

## 🎯 Use Case Navigation

### Use Case: "I want to build a sales bot"
1. **Read**: [README.md](./README.md) - Why Auris?
2. **Setup**: [STARTUP.md](./STARTUP.md) - Get it running
3. **Build**: [WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md) - Workflow 1 & 3
4. **Scale**: [PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md) - Scenario 2

### Use Case: "I need to integrate with my CRM"
1. **Learn API**: [WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md) - Section 6 (API Endpoints)
2. **Integration**: [WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md) - Section 8 (Integration Guide)
3. **Cost**: [PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md) - Scenario 1

### Use Case: "I want to add AI to customer support"
1. **Setup**: [STARTUP.md](./STARTUP.md)
2. **Build Agent**: [WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md) - Workflow 1
3. **Add Knowledge Base**: [WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md) - Workflow 2
4. **Budget**: [PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md) - Scenario 1

### Use Case: "I need to understand pricing"
1. **Start**: [PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md) - Credit System section
2. **Examples**: [PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md) - Scenarios 1-4
3. **Optimize**: [PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md) - Cost Optimization Strategies
4. **Compare**: [PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md) - Competitive Comparison

### Use Case: "I'm deploying to production"
1. **Setup**: [STARTUP.md](./STARTUP.md)
2. **Carrier Integration**: [WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md) - Section 8 (Carrier Config)
3. **AI Vendors**: [WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md) - Section 8 (AI Vendor Config)
4. **Enterprise**: [PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md) - Enterprise Pricing section

### Use Case: "I have a technical problem"
1. **Troubleshoot**: [WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md) - Section 9 (FAQ)
2. **Debug**: Check logs and use [WORKFLOW_DOCUMENTATION.md](./WORKFLOW_DOCUMENTATION.md) - Q4 (Debug Failed Call)

---

## 📊 Documentation Statistics

| Document | Size | Sections | Target Audience | Read Time |
|----------|------|----------|-----------------|-----------|
| README.md | 7.1 KB | 6 | Everyone | 5 min |
| STARTUP.md | 2.8 KB | 5 | Developers | 5 min |
| WORKFLOW_DOCUMENTATION.md | 42 KB | 9 | Technical | 45 min |
| PRICING_AND_COSTS.md | 18 KB | 8 | Finance/Product | 30 min |
| **Total** | **~70 KB** | **28** | **Everyone** | **85 min** |

---

## 🔄 Documentation Update Schedule

| Document | Update Frequency | Last Updated |
|----------|-----------------|-------------|
| README.md | As needed (features) | July 1, 2026 |
| STARTUP.md | As needed (deps) | July 1, 2026 |
| WORKFLOW_DOCUMENTATION.md | Weekly (APIs) | July 21, 2026 |
| PRICING_AND_COSTS.md | Monthly (pricing) | July 21, 2026 |

---

## 🎓 Learning Path

### Beginner Path (1-2 hours)
1. Read: README.md (5 min)
2. Read: Quick Start in STARTUP.md (5 min)
3. Run: `docker compose up postgres redis minio -d` (10 min)
4. Read: Workflow Concepts section of WORKFLOW_DOCUMENTATION.md (15 min)
5. Build: Your first agent using Workflow 1 (30 min)
6. Verify: Make test calls and review transcripts (15 min)

### Intermediate Path (4-6 hours)
1. Complete: Beginner Path (2 hours)
2. Study: All 5 Workflows in WORKFLOW_DOCUMENTATION.md (60 min)
3. Implement: Workflow 2 (RAG) + Workflow 3 (Campaigns) (90 min)
4. Read: Integration Guide section (30 min)
5. Plan: Cost structure from PRICING_AND_COSTS.md (30 min)

### Advanced Path (1-2 days)
1. Complete: Intermediate Path (6 hours)
2. Study: All API endpoints (90 min)
3. Implement: Custom carrier integration (Telnyx/Twilio) (120 min)
4. Build: CRM sync integration (180 min)
5. Deploy: Production environment (120 min)
6. Monitor: Set up cost alerts & analytics (60 min)

---

## 💬 Support & Community

- **GitHub Issues**: Report bugs & feature requests
- **Email**: support@auris.xyz
- **Documentation**: https://docs.auris.xyz
- **Pricing Calculator**: https://auris.xyz/pricing-calculator

---

## ✅ Documentation Checklist

Before going to production, ensure you've read:
- [ ] README.md - Understand platform
- [ ] STARTUP.md - Know how to deploy
- [ ] WORKFLOW_DOCUMENTATION.md (all sections) - Understand APIs
- [ ] PRICING_AND_COSTS.md - Know your costs
- [ ] Integration Guide - Plan integrations
- [ ] Troubleshooting FAQ - Know solutions

---

**Total Documentation Size**: ~70 KB  
**Total Documentation Time**: 85 minutes to read all  
**Last Updated**: July 21, 2026  
**Maintained By**: Venkat Karthik & Zovance
