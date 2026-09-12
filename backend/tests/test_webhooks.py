"""Tests for Webhook Ingestion Endpoints (Meta Instagram & Shopify)"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_meta_webhook_ingestion(client: AsyncClient):
    """Verifies that Instagram webhook payloads are ingested and queued successfully."""
    payload = {
        "account_id": "acc_instagram_01",
        "sender_id": "ig_user_102",
        "sender_name": "Sarah Miller",
        "message_body": "Hello! How much does standard shipping cost to Chicago?",
        "interaction_type": "DM"
    }

    response = await client.post("/api/webhooks/meta", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["platform"] == "INSTAGRAM"
    assert data["interaction_id"].startswith("meta_")
    assert data["account_id"] == "acc_instagram_01"


@pytest.mark.asyncio
async def test_meta_graph_api_schema_ingestion(client: AsyncClient):
    """Verifies standard nested Meta Graph API webhook format compatibility."""
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400",
                "time": 1726000000,
                "messaging": [
                    {
                        "sender": {"id": "ig_cust_883"},
                        "recipient": {"id": "page_123"},
                        "timestamp": 1726000000,
                        "message": {"text": "Is the vegan leather desk mat water resistant?"}
                    }
                ]
            }
        ]
    }

    response = await client.post("/api/webhooks/meta", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["platform"] == "INSTAGRAM"


@pytest.mark.asyncio
async def test_shopify_webhook_ingestion(client: AsyncClient):
    """Verifies Shopify cart/order webhooks are parsed and queued."""
    payload = {
        "topic": "carts/abandoned",
        "account_id": "acc_shopify_01",
        "sender_id": "cust_shopify_901",
        "sender_name": "Marcus Vance",
        "cart_value": 49.99,
        "abandoned_items": ["CleanDesk Dual-Sided Vegan Leather Desk Mat"]
    }

    response = await client.post("/api/webhooks/shopify", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["platform"] == "SHOPIFY"
    assert data["interaction_id"].startswith("shp_")
