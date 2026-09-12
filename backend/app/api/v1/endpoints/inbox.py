"""Universal Inbox Endpoints

Provides filtering, searching, and pagination across multi-platform interactions
(Instagram comments, DMs, Shopify abandoned carts, and order status inquiries).
Also supports human-agent manual replies and message deletion for testing.
"""

from datetime import datetime, timezone
import math
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.db.session import db_manager
from app.models.interaction import InteractionStatus
from app.schemas.interaction import InteractionResponse, ManualReplyRequest, PaginatedInteractionResponse
from app.api.websockets.manager import ws_manager

router = APIRouter()


@router.get("/messages", response_model=PaginatedInteractionResponse)
async def list_inbox_messages(
    platform: Optional[str] = Query(None, description="Filter by platform (INSTAGRAM, SHOPIFY, or omit for all)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (QUEUED, PROCESSING, SENT, FAILED)"),
    risk_only: Optional[bool] = Query(False, description="Filter only flagged/high-risk interactions"),
    search: Optional[str] = Query(None, description="Search term across message text and customer name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Retrieves paginated customer interactions for the Universal Inbox."""
    interactions_col = db_manager.get_collection("interactions")
    query = {}

    if platform and platform.upper() != "ALL":
        query["platform"] = platform.upper()

    if status_filter and status_filter.upper() != "ALL":
        query["status"] = status_filter.upper()

    if risk_only:
        query["risk_flag"] = True

    if search:
        query["message_body"] = {"$regex": search, "$options": "i"}

    total_count = await interactions_col.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

    cursor = interactions_col.find(query).sort("created_at", -1).skip(skip).limit(limit)
    raw_docs = await cursor.to_list(length=limit)

    items = []
    for doc in raw_docs:
        doc_id = str(doc.get("_id") or doc.get("id"))
        items.append(InteractionResponse(
            id=doc_id,
            account_id=doc.get("account_id", ""),
            platform=doc.get("platform", "INSTAGRAM"),
            sender_id=doc.get("sender_id", ""),
            sender_name=doc.get("sender_name", "Customer"),
            message_body=doc.get("message_body", ""),
            interaction_type=doc.get("interaction_type", "DM"),
            status=doc.get("status", InteractionStatus.QUEUED),
            sentiment=doc.get("sentiment", "NEUTRAL"),
            risk_score=doc.get("risk_score", 10),
            risk_flag=doc.get("risk_flag", False),
            risk_reason=doc.get("risk_reason"),
            ai_reply=doc.get("ai_reply"),
            rag_sources=doc.get("rag_sources", []),
            raw_payload=doc.get("raw_payload"),
            created_at=doc.get("created_at") or datetime.now(timezone.utc),
            updated_at=doc.get("updated_at") or datetime.now(timezone.utc)
        ))

    return PaginatedInteractionResponse(
        items=items,
        total=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/messages/{interaction_id}", response_model=InteractionResponse)
async def get_message_detail(interaction_id: str):
    """Fetches details for a single interaction."""
    interactions_col = db_manager.get_collection("interactions")
    doc = await interactions_col.find_one({"_id": interaction_id}) or await interactions_col.find_one({"id": interaction_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")

    return InteractionResponse(
        id=str(doc.get("_id") or doc.get("id")),
        account_id=doc.get("account_id", ""),
        platform=doc.get("platform", "INSTAGRAM"),
        sender_id=doc.get("sender_id", ""),
        sender_name=doc.get("sender_name", "Customer"),
        message_body=doc.get("message_body", ""),
        interaction_type=doc.get("interaction_type", "DM"),
        status=doc.get("status", InteractionStatus.QUEUED),
        sentiment=doc.get("sentiment", "NEUTRAL"),
        risk_score=doc.get("risk_score", 10),
        risk_flag=doc.get("risk_flag", False),
        risk_reason=doc.get("risk_reason"),
        ai_reply=doc.get("ai_reply"),
        rag_sources=doc.get("rag_sources", []),
        raw_payload=doc.get("raw_payload"),
        created_at=doc.get("created_at") or datetime.now(timezone.utc),
        updated_at=doc.get("updated_at") or datetime.now(timezone.utc)
    )


@router.post("/messages/{interaction_id}/reply", response_model=InteractionResponse)
async def manual_reply(interaction_id: str, reply_req: ManualReplyRequest):
    """Allows a human agent to manually override or send a customized response."""
    interactions_col = db_manager.get_collection("interactions")
    doc = await interactions_col.find_one({"_id": interaction_id}) or await interactions_col.find_one({"id": interaction_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction '{interaction_id}' not found in database. It may have been cleared during a database reset. Please refresh your inbox."
        )

    updated_doc = {
        "status": InteractionStatus.SENT,
        "ai_reply": reply_req.reply_body,
        "risk_flag": False,  # Human agent resolved
        "updated_at": datetime.now(timezone.utc)
    }

    await interactions_col.update_one({"_id": doc["_id"]}, {"$set": updated_doc})
    doc.update(updated_doc)
    doc["id"] = str(doc.get("_id") or doc.get("id"))

    # Broadcast update
    await ws_manager.broadcast("INTERACTION_COMPLETED", doc)

    return InteractionResponse(
        id=doc["id"],
        account_id=doc.get("account_id", ""),
        platform=doc.get("platform", "INSTAGRAM"),
        sender_id=doc.get("sender_id", ""),
        sender_name=doc.get("sender_name", "Customer"),
        message_body=doc.get("message_body", ""),
        interaction_type=doc.get("interaction_type", "DM"),
        status=doc.get("status", InteractionStatus.SENT),
        sentiment=doc.get("sentiment", "NEUTRAL"),
        risk_score=doc.get("risk_score", 10),
        risk_flag=doc.get("risk_flag", False),
        risk_reason=doc.get("risk_reason"),
        ai_reply=doc.get("ai_reply"),
        rag_sources=doc.get("rag_sources", []),
        raw_payload=doc.get("raw_payload"),
        created_at=doc.get("created_at") or datetime.now(timezone.utc),
        updated_at=doc.get("updated_at") or datetime.now(timezone.utc)
    )


@router.delete("/messages", status_code=status.HTTP_200_OK)
async def clear_messages():
    """Clears interaction inbox history for clean test runs."""
    interactions_col = db_manager.get_collection("interactions")
    await interactions_col.delete_many({})
    await ws_manager.broadcast("INBOX_CLEARED", {})
    return {"status": "success", "message": "All interactions cleared."}

