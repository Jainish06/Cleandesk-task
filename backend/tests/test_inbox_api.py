"""Tests for Universal Inbox Filtering and Pagination Endpoints"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_inbox_pagination_and_filtering(client: AsyncClient):
    """Verifies that the inbox endpoint correctly paginates and filters messages."""
    # 1. Clear existing messages
    await client.delete("/api/inbox/messages")

    # 2. Ingest 2 Instagram webhooks and 1 Shopify webhook
    await client.post("/api/webhooks/meta", json={
        "sender_name": "Alice IG",
        "message_body": "What are the dimensions of the desk mat?"
    })
    await client.post("/api/webhooks/meta", json={
        "sender_name": "Bob IG",
        "message_body": "Do you ship to London?"
    })
    await client.post("/api/webhooks/shopify", json={
        "topic": "orders/create",
        "sender_name": "Charlie Shp",
        "order_number": 9901
    })

    # 3. Query all messages
    all_res = await client.get("/api/inbox/messages?page=1&limit=10")
    assert all_res.status_code == 200
    all_data = all_res.json()
    assert all_data["total"] == 3
    assert len(all_data["items"]) == 3

    # 4. Filter by platform
    ig_res = await client.get("/api/inbox/messages?platform=INSTAGRAM")
    assert ig_res.status_code == 200
    ig_data = ig_res.json()
    assert ig_data["total"] == 2
    assert all(item["platform"] == "INSTAGRAM" for item in ig_data["items"])

    shp_res = await client.get("/api/inbox/messages?platform=SHOPIFY")
    assert shp_res.status_code == 200
    shp_data = shp_res.json()
    assert shp_data["total"] == 1
    assert shp_data["items"][0]["platform"] == "SHOPIFY"


@pytest.mark.asyncio
async def test_manual_agent_reply_override(client: AsyncClient):
    """Verifies that a human agent can manually send a customized reply."""
    # Ingest a message
    ingest_res = await client.post("/api/webhooks/meta", json={
        "sender_name": "Test Customer",
        "message_body": "Custom inquiry about wholesale bulk pricing."
    })
    interaction_id = ingest_res.json()["interaction_id"]

    # Post manual human reply
    reply_res = await client.post(
        f"/api/inbox/messages/{interaction_id}/reply",
        json={"reply_body": "Hello! For bulk orders over 50 units, we offer custom 30% wholesale discounts."}
    )
    assert reply_res.status_code == 200
    reply_data = reply_res.json()
    assert reply_data["status"] == "SENT"
    assert "wholesale discounts" in reply_data["ai_reply"]
