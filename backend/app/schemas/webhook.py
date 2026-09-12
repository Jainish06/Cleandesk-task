"""Webhook Request Schemas

Supports both standard platform JSON structures (Meta Graph API & Shopify Webhook headers)
and developer-friendly simulated test payloads for easy evaluation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Meta (Instagram) Webhook Schemas
# ---------------------------------------------------------------------------

class MetaWebhookEntryMessaging(BaseModel):
    sender: Optional[Dict[str, str]] = None
    recipient: Optional[Dict[str, str]] = None
    timestamp: Optional[int] = None
    message: Optional[Dict[str, Any]] = None


class MetaWebhookEntryChange(BaseModel):
    field: Optional[str] = None
    value: Optional[Dict[str, Any]] = None


class MetaWebhookEntry(BaseModel):
    id: Optional[str] = None
    time: Optional[int] = None
    messaging: Optional[List[MetaWebhookEntryMessaging]] = None
    changes: Optional[List[MetaWebhookEntryChange]] = None


class MetaWebhookPayload(BaseModel):
    """Standard or Simulated Meta (Instagram) Webhook Payload"""
    object: Optional[str] = "instagram"
    entry: Optional[List[MetaWebhookEntry]] = None

    # Simplified simulation fields for developer test bench
    account_id: Optional[str] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    message_body: Optional[str] = None
    interaction_type: Optional[str] = "DM"  # DM or COMMENT


# ---------------------------------------------------------------------------
# Shopify Webhook Schemas
# ---------------------------------------------------------------------------

class ShopifyLineItem(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    price: Optional[str] = None
    quantity: Optional[int] = None


class ShopifyCustomer(BaseModel):
    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


class ShopifyWebhookPayload(BaseModel):
    """Standard or Simulated Shopify Webhook Payload"""
    topic: Optional[str] = "orders/create"  # orders/create, checkouts/create, carts/abandoned
    id: Optional[int] = None
    order_number: Optional[int] = None
    total_price: Optional[str] = None
    currency: Optional[str] = "USD"
    customer: Optional[ShopifyCustomer] = None
    line_items: Optional[List[ShopifyLineItem]] = None

    # Simplified simulation fields
    account_id: Optional[str] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    message_body: Optional[str] = None
    cart_value: Optional[float] = None
    abandoned_items: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Ingestion Response
# ---------------------------------------------------------------------------

class WebhookResponse(BaseModel):
    status: str = "queued"
    interaction_id: str
    platform: str
    message: str
    account_id: str
    risk_score: int
