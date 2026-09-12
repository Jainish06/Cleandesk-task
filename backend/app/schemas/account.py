"""Account Management Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AccountResponse(BaseModel):
    id: str
    platform: str
    handle: str
    name: str
    daily_limit: int
    sent_today: int
    risk_score: int
    health_status: str
    last_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AccountUpdateRequest(BaseModel):
    daily_limit: Optional[int] = None
    risk_score: Optional[int] = None
    health_status: Optional[str] = None
