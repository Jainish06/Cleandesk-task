"""Webhook Ingestion Endpoints for Meta (Instagram) and Shopify

Ingests simulated or live webhook payloads, normalizes the event data,
persists the record as QUEUED in MongoDB, pushes the job to the Redis queue,
and emits real-time WebSocket notifications to connected dashboards.
"""

from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, HTTPException, status
from app.core.logging import logger
from app.db.session import db_manager
from app.models.interaction import InteractionStatus, InteractionType, SentimentEnum
from app.schemas.webhook import MetaWebhookPayload, ShopifyWebhookPayload, WebhookResponse
from app.services.queue_service import queue_service
from app.services.rate_limiter import rate_limiter
from app.api.websockets.manager import ws_manager

router = APIRouter()


@router.post("/meta", response_model=WebhookResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_meta_webhook(payload: MetaWebhookPayload):
    """Ingests simulated or live Meta (Instagram) comment/DM webhook payloads.

    Supports both Meta Graph API standard JSON schemas and developer test payloads.
    """
    interactions_col = db_manager.get_collection("interactions")
    interaction_id = f"meta_{uuid.uuid4().hex[:12]}"

    # Extract fields from standard Meta Graph API payload if present
    sender_id = payload.sender_id or "user_ig_9921"
    sender_name = payload.sender_name or "Instagram Customer"
    message_body = payload.message_body
    interaction_type = InteractionType.DM

    if payload.entry and len(payload.entry) > 0:
        entry = payload.entry[0]
        # Check Direct Messages
        if entry.messaging and len(entry.messaging) > 0:
            msg_obj = entry.messaging[0]
            sender_id = msg_obj.sender.get("id", sender_id) if msg_obj.sender else sender_id
            if msg_obj.message and "text" in msg_obj.message:
                message_body = msg_obj.message["text"]
            interaction_type = InteractionType.DM
        # Check Comments / Changes
        elif entry.changes and len(entry.changes) > 0:
            change = entry.changes[0]
            val = change.value or {}
            sender_id = val.get("from", {}).get("id", sender_id)
            sender_name = val.get("from", {}).get("username", sender_name)
            message_body = val.get("text", message_body)
            interaction_type = InteractionType.COMMENT

    if not message_body:
        message_body = "Hello, do you offer free shipping to California for the desk mat?"

    account_id = payload.account_id or "acc_instagram_01"

    # Analyze Sentiment & Initial Inbound Risk
    sentiment, risk_delta, risk_flag, risk_reason = rate_limiter.analyze_sentiment_and_risk(message_body)

    interaction_doc = {
        "_id": interaction_id,
        "id": interaction_id,
        "account_id": account_id,
        "platform": "INSTAGRAM",
        "sender_id": sender_id,
        "sender_name": sender_name,
        "message_body": message_body,
        "interaction_type": interaction_type,
        "status": InteractionStatus.QUEUED,
        "sentiment": sentiment,
        "risk_score": 10 + risk_delta,
        "risk_flag": risk_flag,
        "risk_reason": risk_reason,
        "ai_reply": None,
        "rag_sources": [],
        "raw_payload": payload.model_dump(),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    # 1. Save to MongoDB with status QUEUED
    await interactions_col.insert_one(interaction_doc)

    # 2. Push to Redis Event Queue for Asynchronous Worker Processing
    await queue_service.enqueue({
        "interaction_id": interaction_id,
        "account_id": account_id,
        "platform": "INSTAGRAM",
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # 3. Broadcast WebSocket Live Notification
    await ws_manager.broadcast("INTERACTION_CREATED", interaction_doc)

    logger.info(f"Meta webhook ingested and queued: {interaction_id} from {sender_name}")

    return WebhookResponse(
        status="queued",
        interaction_id=interaction_id,
        platform="INSTAGRAM",
        message="Instagram webhook payload received, stored as QUEUED, and pushed to Redis queue.",
        account_id=account_id,
        risk_score=interaction_doc["risk_score"]
    )


@router.post("/shopify", response_model=WebhookResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_shopify_webhook(payload: ShopifyWebhookPayload):
    """Ingests simulated or live Shopify order, checkout, or cart webhook payloads.

    Triggers automated customer service and notification pipeline.
    """
    interactions_col = db_manager.get_collection("interactions")
    interaction_id = f"shp_{uuid.uuid4().hex[:12]}"
    account_id = payload.account_id or "acc_shopify_01"

    topic = payload.topic or "orders/create"
    customer_name = "Shopify Shopper"
    sender_id = payload.sender_id or "cust_shp_4401"

    if payload.customer:
        name_parts = [p for p in [payload.customer.first_name, payload.customer.last_name] if p]
        if name_parts:
            customer_name = " ".join(name_parts)
        if payload.customer.id:
            sender_id = str(payload.customer.id)
    elif payload.sender_name:
        customer_name = payload.sender_name

    # Determine message body based on topic if not explicitly given
    message_body = payload.message_body
    interaction_type = InteractionType.ORDER_UPDATE

    if not message_body:
        if "abandoned" in topic.lower() or payload.abandoned_items:
            items = ", ".join(payload.abandoned_items) if payload.abandoned_items else "CleanDesk Vegan Leather Desk Mat"
            val = f"${payload.cart_value:.2f}" if payload.cart_value else "$49.99"
            message_body = f"Customer abandoned shopping cart ({val}) containing: {items}."
            interaction_type = InteractionType.ABANDONED_CART
        elif "order" in topic.lower():
            order_num = payload.order_number or 1042
            total = payload.total_price or "79.98"
            message_body = f"Order #{order_num} confirmed for {total} USD. Can you confirm when it will arrive?"
            interaction_type = InteractionType.ORDER_UPDATE
        else:
            message_body = f"Shopify store event: {topic}."

    sentiment, risk_delta, risk_flag, risk_reason = rate_limiter.analyze_sentiment_and_risk(message_body)

    interaction_doc = {
        "_id": interaction_id,
        "id": interaction_id,
        "account_id": account_id,
        "platform": "SHOPIFY",
        "sender_id": sender_id,
        "sender_name": customer_name,
        "message_body": message_body,
        "interaction_type": interaction_type,
        "status": InteractionStatus.QUEUED,
        "sentiment": sentiment,
        "risk_score": 10 + risk_delta,
        "risk_flag": risk_flag,
        "risk_reason": risk_reason,
        "ai_reply": None,
        "rag_sources": [],
        "raw_payload": payload.model_dump(),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    # 1. Save to MongoDB
    await interactions_col.insert_one(interaction_doc)

    # 2. Push to Redis Event Queue
    await queue_service.enqueue({
        "interaction_id": interaction_id,
        "account_id": account_id,
        "platform": "SHOPIFY",
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # 3. Broadcast WebSocket Live Notification
    await ws_manager.broadcast("INTERACTION_CREATED", interaction_doc)

    logger.info(f"Shopify webhook ingested and queued: {interaction_id} for {customer_name}")

    return WebhookResponse(
        status="queued",
        interaction_id=interaction_id,
        platform="SHOPIFY",
        message=f"Shopify event ({topic}) ingested and queued for processing.",
        account_id=account_id,
        risk_score=interaction_doc["risk_score"]
    )
