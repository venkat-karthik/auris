# 📚 Auris Backend API Reference

> This document lists all public HTTP endpoints exposed by the **Auris** backend service.  It is intended for developers building front‑ends, integrations, or third‑party services.

---

## 📑 Table of Contents
1. [Authentication & Security](#authentication--security)
2. [Agents API](#agents-api)
3. [API Keys API](#api-keys-api)
4. [Calls & Telephony API](#calls--telephony-api)
5. [Billing API](#billing-api)
6. [Phone Numbers API](#phone-numbers-api)
7. [Campaigns API](#campaigns-api)
8. [Knowledge Base API](#knowledge-base-api)
9. [Rate‑Limiting Middleware](#rate‑limiting-middleware)

---

## 🔐 Authentication & Security
| Header | Value | Description |
|---|---|---|
| **Authorization** | `Bearer <API‑KEY>` | Every request must include a valid API key belonging to the organization. The key is generated via the **API Keys** endpoint. |

> The API key is stored hashed in the database; only the raw key is ever returned at creation time.

---

## 🤖 Agents API  (`/agents`)
| Method | Path | Description | Request Body | Response |
|---|---|---|---|---|
| **POST** | `/agents` | Create a new agent for the organization. | `AgentCreate`<br>`{ name: string, description?: string, graph?: object, model_config_data?: object, context_variables?: object }` | `AgentResponse`<br>`{ id, org_id, name, description, graph, model_config, context_variables }` |
| **GET** | `/agents` | List all active agents. | – | `AgentResponse[]` |
| **GET** | `/agents/{agent_id}` | Retrieve a single agent by ID. | – | `AgentResponse` |
| **PUT** | `/agents/{agent_id}` | Update fields of an existing agent. | `AgentUpdate` (all fields optional) | `AgentResponse` |
| **DELETE** | `/agents/{agent_id}` | Soft‑delete (deactivate) an agent. | – | `204 No Content` |

**Models**
- `AgentCreate` – fields: `name` (required), optional `description`, `graph`, `model_config_data`, `context_variables`.
- `AgentUpdate` – all fields optional, same shape as `AgentCreate`.
- `AgentResponse` – includes `id`, `org_id`, `name`, `description`, `graph`, `model_config` (aliased from `model_config_data`), `context_variables`.

---

## 🗝️ API Keys API (`/api-keys`)
| Method | Path | Description | Request Body | Response |
|---|---|---|---|---|
| **POST** | `/api-keys` | Create a new API key for the organization. Returns the raw secret **once**. | `ApiKeyCreate`<br>`{ name: string }` | `ApiKeyCreatedResponse` – `{ id, name, key_prefix, is_active, created_at, raw_key }` |
| **GET** | `/api-keys` | List active API keys (hashes, prefixes – never the raw secret). | – | `ApiKeyResponse[]` |
| **DELETE** | `/api-keys/{key_id}` | Revoke/archive an API key. | – | `{ message: string, id: number }` |

**Models**
- `ApiKeyCreate`: `{ name: string }`
- `ApiKeyResponse`: `{ id, name, key_prefix, is_active, created_at }`
- `ApiKeyCreatedResponse` extends the above with `raw_key` (returned only on creation).

---

## 📞 Calls & Telephony API (`/calls` & `/telephony`)
### Calls (`/calls`)
| Method | Path | Description |
|---|---|---|
| **GET** | `/calls` | List recent call logs for the organization. |
| **GET** | `/calls/{call_id}` | Retrieve detailed call metadata and transcript. |
| **POST** | `/calls` | (If implemented) Initiate a new call via Telnyx.

### Telephony WebSocket (`/telephony/ws/telnyx`)
WebSocket endpoint used by the front‑end to stream audio frames to the backend and receive generated audio.
- **Query parameters**: `call_control_id` (Telnyx call ID), `org_id`, `agent_id`, optional `from` and `to` phone numbers.
- **Message flow**: client sends binary PCM frames; backend forwards to the pipeline, receives LLM‑generated audio and sends back binary frames.

---

## 💰 Billing API (`/billing`)
| Method | Path | Description |
|---|---|---|
| **GET** | `/billing/summary` | Returns current organization credit balance and usage statistics. |
| **POST** | `/billing/top‑up` | Add credit to the organization (integrated with Razorpay). |
| **GET** | `/billing/transactions` | List all billing transactions (charges, refunds, top‑ups). |

---

## 📞 Phone Numbers API (`/phone-numbers`)
| Method | Path | Description |
|---|---|---|
| **GET** | `/phone-numbers` | List available virtual numbers that can be leased. |
| **POST** | `/phone-numbers/lease` | Lease a number for the organization. |
| **POST** | `/phone-numbers/bind` | Bind a leased number to a specific agent/call flow. |
| **POST** | `/phone-numbers/release` | Release a previously leased number. |

---

## 📣 Campaigns API (`/campaigns`)
| Method | Path | Description |
|---|---|---|
| **POST** | `/campaigns` | Create a new outbound campaign (list of contacts, schedule, assigned agent). |
| **GET** | `/campaigns` | List campaigns belonging to the organization. |
| **GET** | `/campaigns/{campaign_id}` | Retrieve campaign details and progress stats. |
| **PUT** | `/campaigns/{campaign_id}` | Update campaign configuration. |
| **DELETE** | `/campaigns/{campaign_id}` | Archive a campaign.

---

## 📚 Knowledge Base API (`/knowledge-base`)
| Method | Path | Description |
|---|---|---|
| **POST** | `/knowledge-base` | Upload a new document (PDF, txt, etc.) that will be indexed with pgvector. |
| **GET** | `/knowledge-base` | List indexed documents. |
| **GET** | `/knowledge-base/{doc_id}` | Retrieve document metadata. |
| **DELETE** | `/knowledge-base/{doc_id}` | Delete a document from the vector store.

---

## ⏱️ Rate‑Limiting Middleware (`/dependencies/rate_limit.py`)
All write‑heavy endpoints (e.g., `/calls`, `/agents`, `/campaigns`, `/api-keys`) are protected by a **Redis sliding‑window limiter**.  The default quota is **60 requests per minute per organization** but can be tuned via the `RATE_LIMIT` environment variable.

---

## 📦 How to Use the API
1. **Generate an API key** via `POST /api-keys` (requires an admin user). Store the raw key securely.
2. **Include the key** in the `Authorization: Bearer <key>` header for every request.
3. **Interact with agents** – create an agent, then start a call using the Telephony WebSocket.  The backend will stream audio to the pipeline, invoke the selected LLM/TTS providers, and return generated audio frames in real‑time.
4. **Monitor usage** – call `/billing/summary` to keep track of minutes consumed and remaining credit.
5. **Scale** – you can spin up multiple FastAPI workers behind a load balancer; the Redis rate‑limiter works across all instances.

---

## 📄 Full OpenAPI Spec
The FastAPI application automatically generates an OpenAPI schema at:
```
GET /api/v1/openapi.json
```
You can import this JSON into tools like **Postman**, **Insomnia**, or **Swagger UI** (`/api/v1/docs`).

---

*Generated on $(date)*
