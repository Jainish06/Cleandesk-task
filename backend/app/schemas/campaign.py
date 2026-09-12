"""Campaign Dispatch Schemas

Handles bulk outbound campaign dispatch requests with account pacing and safe background queuing.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CampaignRecipient(BaseModel):
    recipient_id: str
    recipient_name: str
    custom_message: Optional[str] = None


class CampaignDispatchRequest(BaseModel):
    account_id: str
    campaign_name: str
    platform: str = "INSTAGRAM"
    template_message: str
    recipients: List[CampaignRecipient] = Field(..., min_length=1)
    pacing_delay_ms: Optional[int] = 500


class CampaignDispatchResponse(BaseModel):
    campaign_id: str
    status: str = "QUEUED"
    total_queued: int
    account_id: str
    estimated_duration_seconds: float
    message: str
