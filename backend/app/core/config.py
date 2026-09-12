"""Application Configuration Module

Uses Pydantic BaseSettings for type-safe environment variable parsing
and defaults for MongoDB, Redis, Gemini AI, and rate limiting thresholds.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server Info
    PROJECT_NAME: str = "CleanDesk Event-Driven Messaging Pipeline"
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # MongoDB Settings
    MONGODB_URI: Optional[str] = ""
    MONGODB_DB_NAME: str = "cleandesk_pipeline"

    # Redis Queue Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TOKEN: Optional[str] = ""
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = ""
    REDIS_QUEUE_NAME: str = "cleandesk:interactions:queue"
    REDIS_DLQ_NAME: str = "cleandesk:interactions:dlq"

    # Gemini AI Settings
    GEMINI_API_KEY: Optional[str] = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Rate Limiting & Account Health Protection
    MAX_DAILY_QUOTA_DEFAULT: int = 50
    RISK_THRESHOLD_REJECTION: int = 80
    INTER_MESSAGE_PACING_MS: int = 750


settings = Settings()
