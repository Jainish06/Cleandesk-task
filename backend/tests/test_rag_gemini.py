"""Tests for RAG Knowledge Base and AI Response Generation"""

import pytest
from httpx import AsyncClient
from app.services.rag_service import rag_service


@pytest.mark.asyncio
async def test_semantic_context_retrieval():
    """Verifies that RAG retrieval surfaces the correct store policies and products."""
    # Query 1: Shipping
    shipping_docs = await rag_service.retrieve_context("How long does delivery take to Canada?")
    assert len(shipping_docs) > 0
    top_doc_name = shipping_docs[0]["product_name"]
    assert "shipping" in top_doc_name.lower() or "delivery" in top_doc_name.lower()

    # Query 2: Returns & Refunds
    return_docs = await rag_service.retrieve_context("Can I return this if I don't like it?")
    assert len(return_docs) > 0
    assert "return" in return_docs[0]["product_name"].lower()


@pytest.mark.asyncio
async def test_ai_generate_reply_endpoint(client: AsyncClient):
    """Verifies the on-demand AI reply generation API endpoint."""
    payload = {
        "query": "What discount codes do you have for new buyers?",
        "platform": "INSTAGRAM",
        "customer_name": "Elena Rostova"
    }

    response = await client.post("/api/ai/generate-reply", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 10
    assert "sources" in data
    assert any("discount" in s.lower() for s in data["sources"])


@pytest.mark.asyncio
async def test_knowledge_base_crud(client: AsyncClient):
    """Verifies indexing of new knowledge documents."""
    new_doc = {
        "product_name": "CleanDesk Bamboo Monitor Stand",
        "category": "PRODUCT",
        "context_text": "Retail price is $59.99. Holds up to 45 lbs with a dedicated keyboard stowaway slot underneath."
    }

    create_res = await client.post("/api/ai/knowledge", json=new_doc)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["product_name"] == "CleanDesk Bamboo Monitor Stand"

    list_res = await client.get("/api/ai/knowledge")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(item["product_name"] == "CleanDesk Bamboo Monitor Stand" for item in items)
