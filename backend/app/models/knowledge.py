"""Product Knowledge Base Data Model

Stores catalog items, store policies, shipping/return rules, and warranty FAQs
along with dense vector embeddings for RAG retrieval during AI response generation.
"""

from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field


class ProductKnowledgeBaseModel(BaseModel):
    id: str = Field(default_factory=lambda: "", alias="_id")
    product_name: str
    category: str = "PRODUCT"
    context_text: str
    embedding_data: List[float] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda dt: dt.isoformat()}
    }
