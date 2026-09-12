"""AI & RAG Request and Response Schemas"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AIReplyRequest(BaseModel):
    query: str = Field(..., description="Customer message or comment to respond to")
    platform: str = Field(default="INSTAGRAM", description="Target platform (INSTAGRAM or SHOPIFY)")
    customer_name: Optional[str] = Field(default="Valued Customer", description="Recipient customer name")
    account_id: Optional[str] = None


class AIReplyResponse(BaseModel):
    reply: str
    sources: List[str] = Field(default_factory=list)
    model_used: str
    confidence_score: float = 0.95


class KnowledgeCreateRequest(BaseModel):
    product_name: str
    category: str = "PRODUCT"  # POLICY, PRODUCT, FAQ, DISCOUNT
    context_text: str


class KnowledgeResponse(BaseModel):
    id: str
    product_name: str
    category: str
    context_text: str
    created_at: datetime
