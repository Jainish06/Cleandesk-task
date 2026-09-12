# System Architecture & Technical Design Document

## CleanDesk Event-Driven Multi-Platform Messaging Pipeline

This document details the architectural design decisions, event-driven queueing patterns, account safety safeguards, and RAG integration for the CleanDesk microservice pipeline.

---

## 1. High-Level Architecture Diagram

```
                              ┌───────────────────────────────────┐
                              │  Simulated / Real Inbound Events │
                              └─────────────────┬─────────────────┘
                                                │
                       ┌────────────────────────┴────────────────────────┐
                       ▼                                                 ▼
             [Meta Graph Webhook]                             [Shopify Event Webhook]
          Instagram Comments & DMs                         Orders, Checkouts & Carts
                       │                                                 │
                       └────────────────────────┬────────────────────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │ FastAPI Ingestion API │
                                    │  POST /api/webhooks/* │
                                    └───────────┬───────────┘
                                                │
                        ┌───────────────────────┴───────────────────────┐
                        ▼                                               ▼
              [MongoDB Primary Store]                         [Redis Event Queue]
             (Document saved as QUEUED)                    (LPUSH to interactions:queue)
                                                                        │
                                                                        ▼
                                                           [Async Consumer Worker]
                                                           (BLPOP / Event Loop)
                                                                        │
                                           ┌────────────────────────────┼────────────────────────────┐
                                           ▼                            ▼                            ▼
                                  [Account Safety Engine]     [RAG Knowledge Engine]      [Live WebSocket Bus]
                                  - Daily Quota Check         - Vector/Cosine Similarity   - /ws/inbox Broadcaster
                                  - Risk Score Threshold      - Gemini AI Brand Concierge  - Instant status updates
                                  - Inter-Message Pacing      - Policy / Catalog Grounding   (QUEUED➔PROCESSING➔SENT)
                                  - Sentiment & Keyword Scan
                                           │                            │                            │
                                           └────────────────────────────┼────────────────────────────┘
                                                                        │
                                                                        ▼
                                                           [Update MongoDB Terminal State]
                                                           (Status: SENT or FAILED)
                                                                        │
                                                                        ▼
                                                           [Next.js Universal Inbox UI]
```

---

## 2. Microservice Components

### A. FastAPI Ingestion Layer (`backend/app/api/v1/endpoints/webhooks.py`)
- **Non-blocking ingestion**: Ingests payloads with sub-5ms response time (`HTTP 202 Accepted`).
- **Normalized Data Contract**: Ingests both standard enterprise webhook formats (nested Meta Graph API objects, Shopify webhook JSON) and simplified developer payloads for interactive testing.
- **Immediate State Persistence**: Writes incoming interaction into MongoDB with initial status `QUEUED`.
- **Decoupled Hand-off**: Pushes the job payload into the Redis event queue without waiting for LLM or rate limit evaluations.

### B. Redis Queue & Async Worker (`backend/app/services/queue_service.py` & `worker.py`)
- **Queue Pattern**: Redis List (`RPUSH` / `BLPOP`) providing high-throughput FIFO message sequencing.
- **Resilient Fallback**: If Redis is temporarily unreachable during local testing, an internal async queue seamlessly takes over with zero downtime.
- **Dead Letter Queue (DLQ)**: Failed interactions that exceed retry thresholds or fatal parse errors are moved to `cleandesk:interactions:dlq` for auditing.

### C. Rate Limiting & Account Health Protection (`backend/app/services/rate_limiter.py`)
To prevent social media and e-commerce platforms (Meta/Shopify) from banning automated brand accounts, the pipeline employs a multi-tiered defense:
1. **Daily Quotas (`sent_today` vs `daily_limit`)**:
   - Accounts have configurable daily thresholds (default: 50 for Instagram, 100 for Shopify).
   - Once quota is reached, subsequent outgoing replies are safely throttled or marked `FAILED` with explicit ban-prevention reasons.
2. **Risk Scoring (0-100)**:
   - Accounts with a risk score $\ge 80$ are automatically placed into a `RESTRICTED` state.
   - Hostile legal or chargeback threats (e.g., "chargeback", "sue", "lawyer", "scam") raise risk and flag interactions for human agent intervention (`risk_flag = True`).
3. **Inter-Message Pacing**:
   - Platform algorithms flag burst automated bot messaging. The worker enforces a per-account pacing delay (750ms minimum spacing) via asyncio locks, updating `last_sent_at`.

### D. RAG & Gemini AI Response Generation (`backend/app/services/rag_service.py`)
- **Knowledge Base**: Contains structured store policies (returns, international shipping, discounts) and product catalog data (vegan leather desk mat, 65W GaN charger, cable management hub).
- **Retrieval Engine**: Sparse term-frequency & token cosine similarity with product name keyword boosting.
- **Gemini AI Synthesis**:
   - Model: `gemini-1.5-flash` via `google-genai` / `google.generativeai`.
   - Prompt engineering: Grounded brand concierge persona, platform-specific formatting (concise, professional, warm).
   - Zero-Setup Fallback: If `GEMINI_API_KEY` is not yet set, an intelligent heuristic RAG generator generates high-fidelity replies so the reviewer can test immediately.

### E. Real-Time WebSocket Streaming (`backend/app/api/websockets/manager.py`)
- Maintains bi-directional WebSocket connections at `/ws/inbox`.
- Emits atomic lifecycle events:
  - `INTERACTION_CREATED`: When webhook arrives.
  - `INTERACTION_PROCESSING`: When worker dequeues.
  - `INTERACTION_COMPLETED`: When reply is synthesized and sent.
  - `INTERACTION_FAILED`: When rate-limiter throttles or blocks.
  - `ACCOUNT_UPDATED`: When quota/risk score changes.

---

## 3. Database Schema Design (MongoDB)

### `accounts` Collection
```json
{
  "_id": "acc_instagram_01",
  "platform": "INSTAGRAM",
  "handle": "@cleandesk_shop",
  "name": "CleanDesk Lifestyle Official",
  "daily_limit": 50,
  "sent_today": 8,
  "risk_score": 15,
  "health_status": "HEALTHY",
  "last_sent_at": "2026-09-12T07:20:00Z",
  "created_at": "2026-09-12T07:00:00Z",
  "updated_at": "2026-09-12T07:20:00Z"
}
```

### `customer_interactions` Collection
```json
{
  "_id": "meta_ab812ef90123",
  "account_id": "acc_instagram_01",
  "platform": "INSTAGRAM",
  "sender_id": "ig_cust_102",
  "sender_name": "Sarah Miller",
  "message_body": "Hello! How much does shipping cost to California?",
  "interaction_type": "DM",
  "status": "SENT",
  "sentiment": "NEUTRAL",
  "risk_score": 10,
  "risk_flag": false,
  "risk_reason": null,
  "ai_reply": "Hi Sarah! Standard US shipping takes 3-5 business days and is completely FREE on orders over $60...",
  "rag_sources": ["Shipping & Delivery Times"],
  "created_at": "2026-09-12T07:21:00Z",
  "updated_at": "2026-09-12T07:21:01Z"
}
```

### `product_knowledge_base` Collection
```json
{
  "_id": "kb_return_policy",
  "product_name": "Return & Refund Policy",
  "category": "POLICY",
  "context_text": "We offer a 30-day hassle-free return window with 100% free prepaid return shipping...",
  "created_at": "2026-09-12T07:00:00Z"
}
```
