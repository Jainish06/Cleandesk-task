"""Interaction Schemas for Inbox Queries and Responses"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InteractionResponse(BaseModel):
    id: str
    account_id: str
    platform: str
    sender_id: str
    sender_name: str
    message_body: str
    interaction_type: str
    status: str
    sentiment: str
    risk_score: int
    risk_flag: bool
    risk_reason: Optional[str] = None
    ai_reply: Optional[str] = None
    rag_sources: List[str] = Field(default_factory=list)
    raw_payload: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class PaginatedInteractionResponse(BaseModel):
    items: List[InteractionResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class ManualReplyRequest(BaseModel):
    reply_body: str
