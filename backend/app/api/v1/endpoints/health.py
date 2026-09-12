"""System Health & Diagnostics Endpoint"""

from fastapi import APIRouter
from app.core.config import settings
from app.db.session import db_manager
from app.services.queue_service import queue_service

router = APIRouter()


@router.get("/health")
async def health_check():
    """Returns microservice health, queue backlog size, and connection modes."""
    queue_size = await queue_service.get_queue_size()

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": {
            "type": "mongodb",
            "connected_to_live_mongo": db_manager.is_connected_to_real_mongo,
            "configured_uri": bool((settings.MONGODB_URI or "").strip())
        },
        "queue": {
            "type": "redis",
            "connected_to_live_redis": queue_service.is_connected_to_real_redis,
            "pending_items": queue_size
        },
        "ai": {
            "gemini_api_key_configured": bool((settings.GEMINI_API_KEY or "").strip()),
            "model": settings.GEMINI_MODEL
        }
    }
