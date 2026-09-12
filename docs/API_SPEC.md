# CleanDesk Messaging Pipeline API Specification

Complete reference of all REST endpoints and WebSocket protocols exposed by the FastAPI microservice.

---

## Base URL
- Local: `http://localhost:8000/api`
- WebSocket: `ws://localhost:8000/ws/inbox`

---

## 1. Webhooks Ingestion

### `POST /api/webhooks/meta`
Ingests simulated or production Instagram comment / direct message payloads.

**Status Code**: `202 Accepted`

**Sample Request Body (Simplified Simulation)**:
```json
{
  "account_id": "acc_instagram_01",
  "sender_id": "ig_cust_201",
  "sender_name": "Elena Rostova",
  "message_body": "What are the dimensions of the desk mat?",
  "interaction_type": "DM"
}
```

**Sample Response**:
```json
{
  "status": "queued",
  "interaction_id": "meta_9f81a7b2c01e",
  "platform": "INSTAGRAM",
  "message": "Instagram webhook payload received, stored as QUEUED, and pushed to Redis queue.",
  "account_id": "acc_instagram_01",
  "risk_score": 10
}
```

---

### `POST /api/webhooks/shopify`
Ingests Shopify store events (orders, checkouts, abandoned cart recoveries).

**Status Code**: `202 Accepted`

**Sample Request Body**:
```json
{
  "topic": "carts/abandoned",
  "account_id": "acc_shopify_01",
  "sender_name": "Marcus Vance",
  "cart_value": 49.99,
  "abandoned_items": ["CleanDesk Dual-Sided Vegan Leather Desk Mat"]
}
```

**Sample Response**:
```json
{
  "status": "queued",
  "interaction_id": "shp_812a0ccb19ef",
  "platform": "SHOPIFY",
  "message": "Shopify event (carts/abandoned) ingested and queued for processing.",
  "account_id": "acc_shopify_01",
  "risk_score": 10
}
```

---

## 2. Universal Inbox

### `GET /api/inbox/messages`
Retrieves paginated interactions across platforms with filtering.

**Query Parameters**:
- `platform` (optional): `INSTAGRAM`, `SHOPIFY`, or omit for all.
- `status` (optional): `QUEUED`, `PROCESSING`, `SENT`, `FAILED`.
- `risk_only` (optional): `true` to view only flagged interactions.
- `search` (optional): Text search keyword.
- `page` (int, default: 1): Page number.
- `limit` (int, default: 20): Items per page.

**Sample Response**:
```json
{
  "items": [
    {
      "id": "meta_9f81a7b2c01e",
      "account_id": "acc_instagram_01",
      "platform": "INSTAGRAM",
      "sender_id": "ig_cust_201",
      "sender_name": "Elena Rostova",
      "message_body": "What are the dimensions of the desk mat?",
      "interaction_type": "DM",
      "status": "SENT",
      "sentiment": "NEUTRAL",
      "risk_score": 10,
      "risk_flag": false,
      "risk_reason": null,
      "ai_reply": "Hi Elena! The CleanDesk Vegan Leather Desk Mat measures 90cm x 40cm...",
      "rag_sources": ["CleanDesk Dual-Sided Vegan Leather Desk Mat"],
      "created_at": "2026-09-12T07:20:00Z",
      "updated_at": "2026-09-12T07:20:01Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20,
  "total_pages": 1
}
```

---

### `POST /api/inbox/messages/{id}/reply`
Allows human agent manual override and reply.

**Request Body**:
```json
{
  "reply_body": "Hi Marcus! Here is a direct link to complete your checkout with 15% discount applied."
}
```

---

## 3. Campaign Dispatch

### `POST /api/campaigns/dispatch`
Dispatches bulk outbound messages with asynchronous queuing and inter-message pacing.

**Status Code**: `202 Accepted`

**Sample Request**:
```json
{
  "account_id": "acc_instagram_01",
  "campaign_name": "VIP Autumn Drop",
  "platform": "INSTAGRAM",
  "template_message": "Hi {name}! Check out our new workspace collection with code WELCOME15.",
  "recipients": [
    { "recipient_id": "ig_user_1", "recipient_name": "Sarah" },
    { "recipient_id": "ig_user_2", "recipient_name": "David" }
  ],
  "pacing_delay_ms": 500
}
```

---

## 4. AI & Knowledge Base

### `POST /api/ai/generate-reply`
Generates an on-demand brand-aware reply using RAG and Gemini AI.

**Request Body**:
```json
{
  "query": "Can I return an opened desk mat?",
  "platform": "INSTAGRAM",
  "customer_name": "Alex"
}
```

**Response**:
```json
{
  "reply": "Hi Alex! Yes, CleanDesk provides a 30-day hassle-free return window with 100% free return shipping within the US...",
  "sources": ["Return & Refund Policy"],
  "model_used": "Google Gemini (gemini-1.5-flash)",
  "confidence_score": 0.96
}
```

---

## 5. Account Health & Safety

### `GET /api/accounts`
Lists connected accounts and live risk metrics.

### `POST /api/accounts/{account_id}/reset`
Resets message counters and risk scores to default safe status (for testing).

---

## 6. Real-Time WebSockets

### `WS /ws/inbox`
Subscribes to live inbound interactions, worker progress, and account updates.

**Incoming Event Example**:
```json
{
  "event": "INTERACTION_COMPLETED",
  "data": {
    "id": "meta_9f81a7b2c01e",
    "status": "SENT",
    "ai_reply": "Hi Elena!...",
    "rag_sources": ["CleanDesk Dual-Sided Vegan Leather Desk Mat"]
  }
}
```
