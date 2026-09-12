"""Account Data Model

Represents a connected Instagram or Shopify business account with health metrics,
rate limits, daily quotas, and risk scoring to prevent account bans.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PlatformEnum(str, Enum):
    INSTAGRAM = "INSTAGRAM"
    SHOPIFY = "SHOPIFY"


class AccountHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    RESTRICTED = "RESTRICTED"


class AccountModel(BaseModel):
    id: str = Field(default_factory=lambda: "", alias="_id")
    platform: PlatformEnum
    handle: str
    name: str
    daily_limit: int = 50
    sent_today: int = 0
    risk_score: int = Field(default=10, ge=0, le=100)
    health_status: AccountHealthStatus = AccountHealthStatus.HEALTHY
    last_sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda dt: dt.isoformat()}
    }
