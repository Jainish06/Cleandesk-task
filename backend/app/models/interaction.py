"""Customer Interaction Data Model

Represents inbound social media comments, direct messages, or e-commerce events.
Tracks the end-to-end lifecycle from ingestion (QUEUED) to RAG enrichment (PROCESSING)
to rate-limited delivery (SENT/FAILED).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class InteractionStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    FAILED = "FAILED"


class InteractionType(str, Enum):
    COMMENT = "COMMENT"
    DM = "DM"
    ABANDONED_CART = "ABANDONED_CART"
    ORDER_UPDATE = "ORDER_UPDATE"
    CAMPAIGN = "CAMPAIGN"


class SentimentEnum(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    URGENT = "URGENT"


class CustomerInteractionModel(BaseModel):
    id: str = Field(default_factory=lambda: "", alias="_id")
    account_id: str
    platform: str
    sender_id: str
    sender_name: str
    message_body: str
    interaction_type: InteractionType = InteractionType.DM
    status: InteractionStatus = InteractionStatus.QUEUED
    sentiment: SentimentEnum = SentimentEnum.NEUTRAL
    risk_score: int = 10
    risk_flag: bool = False
    risk_reason: Optional[str] = None
    ai_reply: Optional[str] = None
    rag_sources: List[str] = Field(default_factory=list)
    raw_payload: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda dt: dt.isoformat()}
    }
