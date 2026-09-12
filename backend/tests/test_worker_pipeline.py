"""End-to-End Test for the Asynchronous Queue Worker Pipeline"""

import asyncio
import pytest
from httpx import AsyncClient
from app.db.session import db_manager
from app.models.interaction import InteractionStatus
from app.services.worker import queue_worker


@pytest.mark.asyncio
async def test_end_to_end_worker_enrichment_pipeline(client: AsyncClient):
    """Verifies that an ingested webhook is processed by the async queue worker,

    evaluates rate-limiting, enriches with RAG/Gemini AI, and marks status as SENT.
    """
    # 1. Reset account to healthy state for test isolation
    accounts_col = db_manager.get_collection("accounts")
    await accounts_col.update_one(
        {"_id": "acc_instagram_01"},
        {"$set": {"risk_score": 10, "sent_today": 0, "daily_limit": 50, "health_status": "HEALTHY"}}
    )

    # 2. Start worker
    queue_worker.start()

    # 2. Ingest customer inquiry
    ingest_res = await client.post("/api/webhooks/meta", json={
        "sender_name": "David Kim",
        "message_body": "What is the return policy for the vegan leather desk mat?"
    })
    assert ingest_res.status_code == 202
    interaction_id = ingest_res.json()["interaction_id"]

    # 3. Allow worker task to process the queued item
    interactions_col = db_manager.get_collection("interactions")
    max_retries = 20
    processed = False

    for _ in range(max_retries):
        await asyncio.sleep(0.1)
        doc = await interactions_col.find_one({"_id": interaction_id})
        if doc and doc.get("status") in [InteractionStatus.SENT, InteractionStatus.FAILED]:
            processed = True
            assert doc["status"] == InteractionStatus.SENT
            assert doc["ai_reply"] is not None
            assert len(doc["ai_reply"]) > 10
            assert "Return & Refund Policy" in doc.get("rag_sources", [])
            break

    assert processed is True, "Interaction was not processed by worker within timeout"

    # 4. Stop worker
    await queue_worker.stop()
