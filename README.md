# Auris — Voice AI Platform

Built from scratch. 100% owned by you.

## What Is Auris

Auris is a voice AI platform that lets businesses deploy conversational AI agents
that speak over phone calls and browser WebRTC sessions.

Supports: English, Hindi, Telugu, Tamil (and more Indian languages via Sarvam AI).

## Architecture

```
auris/
├── backend/           # Python + FastAPI
│   ├── app/
│   │   ├── core/      # Config, DB, Security
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── routes/    # API endpoints
│   │   ├── services/
│   │   │   └── pipeline/   # Custom voice pipeline (STT→LLM→TTS)
│   │   └── main.py
│   ├── alembic/       # DB migrations
│   └── requirements.txt
├── frontend/          # Next.js (coming next)
└── docker-compose.yml
```

## Voice Pipeline

The core of Auris — written from scratch, no third-party pipeline framework.

```
Audio In → STT → LLM → TTS → Audio Out
```

Each stage is a `BaseProcessor` that reads from an async queue and writes to the next.
The `PipelineEngine` wires them together and runs them concurrently.

### Supported Providers

| Language  | STT         | LLM                    | TTS           |
|-----------|-------------|------------------------|---------------|
| English   | Deepgram    | OpenAI / Groq          | ElevenLabs    |
| Hindi     | Sarvam      | OpenAI / Groq          | Sarvam Bulbul |
| Telugu    | Sarvam      | OpenAI / Groq          | Sarvam Bulbul |
| Tamil     | Sarvam      | OpenAI / Groq          | Sarvam Bulbul |

## Quick Start

```bash
# 1. Start services
cd auris
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# 2. Start Docker services (Postgres, Redis, MinIO)
docker compose up postgres redis minio -d

# 3. Install Python deps
cd backend
python -m venv venv
venv\Scripts\activate     # Windows
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Start API
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/api/v1/docs

## API Endpoints

### Auth
- `POST /api/v1/auth/signup` — create account + org
- `POST /api/v1/auth/login` — get JWT token
- `GET  /api/v1/auth/me` — current user

### Agents
- `POST   /api/v1/agents` — create agent
- `GET    /api/v1/agents` — list agents
- `GET    /api/v1/agents/{id}` — get agent
- `PUT    /api/v1/agents/{id}` — update agent
- `DELETE /api/v1/agents/{id}` — archive agent

### Calls
- `GET /api/v1/calls` — call history
- `GET /api/v1/calls/{id}` — call detail
- `WS  /api/v1/calls/ws/{agent_id}?token=<jwt>` — WebRTC voice call

### Health
- `GET /api/v1/health`

## Making a Voice Call (WebSocket Protocol)

```javascript
const ws = new WebSocket(`ws://localhost:8000/api/v1/calls/ws/1?token=${jwt}`);

// Start the call
ws.send(JSON.stringify({
  type: "start",
  context: { customer_name: "Raj" }
}));

// Send audio (16kHz mono PCM, base64 encoded)
ws.send(JSON.stringify({
  type: "audio",
  data: btoa(String.fromCharCode(...pcmBytes))
}));

// Receive audio from agent
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === "audio") {
    // Play msg.data (base64 PCM)
  }
  if (msg.type === "transcript") {
    console.log(msg.text, msg.final);
  }
};

// End call
ws.send(JSON.stringify({ type: "end" }));
```

## Cost Tiers

Set `cost_tier` in agent `model_config`:

| Tier     | LLM           | Cost/min (~) |
|----------|---------------|--------------|
| economy  | Groq Llama    | ~₹0.01       |
| standard | GPT-4o-mini   | ~₹0.04       |
| premium  | GPT-4o        | ~₹0.09       |

## What's Next

- [ ] Frontend dashboard (Next.js)
- [ ] Telephony (Telnyx inbound/outbound)
- [ ] Billing (Razorpay — already designed)
- [ ] Customer memory
- [ ] Knowledge base (RAG)
- [ ] Campaigns (outbound dialer)
