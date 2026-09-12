"""AI & RAG Knowledge Endpoints

Provides direct on-demand AI response generation endpoints using Google Gemini
and RAG retrieval over indexed product knowledge documents and store policies.
"""

from datetime import datetime, timezone
from typing import List
import uuid
from fastapi import APIRouter, HTTPException, status
from app.db.session import db_manager
from app.schemas.ai import AIReplyRequest, AIReplyResponse, KnowledgeCreateRequest, KnowledgeResponse
from app.services.rag_service import rag_service

router = APIRouter()


@router.post("/generate-reply", response_model=AIReplyResponse)
async def generate_ai_reply(request: AIReplyRequest):
    """Generates an AI brand response using semantic RAG retrieval and Gemini AI."""
    result = await rag_service.generate_reply(
        query=request.query,
        platform=request.platform,
        customer_name=request.customer_name or "Valued Customer",
        account_id=request.account_id
    )

    return AIReplyResponse(
        reply=result["reply"],
        sources=result["sources"],
        model_used=result["model_used"],
        confidence_score=result["confidence_score"]
    )


@router.get("/knowledge", response_model=List[KnowledgeResponse])
async def list_knowledge_items():
    """Retrieves all indexed product documents, FAQs, and store policies."""
    knowledge_col = db_manager.get_collection("knowledge_base")
    docs = await knowledge_col.find({}).to_list(length=100)
    
    res = []
    for d in docs:
        res.append(KnowledgeResponse(
            id=str(d.get("_id") or d.get("id")),
            product_name=d.get("product_name", "Untitled"),
            category=d.get("category", "PRODUCT"),
            context_text=d.get("context_text", ""),
            created_at=d.get("created_at") or datetime.now(timezone.utc)
        ))
    return res


@router.post("/knowledge", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_item(req: KnowledgeCreateRequest):
    """Indexes a new product document or policy into the RAG knowledge base."""
    knowledge_col = db_manager.get_collection("knowledge_base")
    kb_id = f"kb_{uuid.uuid4().hex[:8]}"

    doc = {
        "_id": kb_id,
        "id": kb_id,
        "product_name": req.product_name,
        "category": req.category.upper(),
        "context_text": req.context_text,
        "embedding_data": [],
        "created_at": datetime.now(timezone.utc)
    }

    await knowledge_col.insert_one(doc)

    return KnowledgeResponse(
        id=kb_id,
        product_name=doc["product_name"],
        category=doc["category"],
        context_text=doc["context_text"],
        created_at=doc["created_at"]
    )
