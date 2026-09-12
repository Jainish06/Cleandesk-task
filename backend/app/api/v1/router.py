"""API v1 Central Router"""

from fastapi import APIRouter
from app.api.v1.endpoints import accounts, ai, campaigns, health, inbox, webhooks

api_router = APIRouter()

api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks Ingestion"])
api_router.include_router(inbox.router, prefix="/inbox", tags=["Universal Inbox"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaign Dispatch"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI & RAG"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Account Health"])
api_router.include_router(health.router, tags=["Diagnostics"])
