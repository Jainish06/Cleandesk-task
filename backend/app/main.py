"""Main FastAPI Application Entrypoint

Configures FastAPI with async lifespan management, CORS middleware,
WebSocket live streaming, and mounts the API v1 router.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.api.websockets.manager import ws_manager
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.db.init_db import seed_database
from app.db.session import db_manager
from app.services.queue_service import queue_service
from app.services.worker import queue_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages async startup and shutdown lifecycle for database and background queue worker."""
    setup_logging()
    logger.info("Initializing CleanDesk Event-Driven Messaging Pipeline...")

    # 1. Connect to MongoDB and seed initial data
    await db_manager.connect()
    await seed_database()

    # 2. Connect to Redis Queue
    await queue_service.connect()

    # 3. Start Asynchronous Queue Consumer Worker
    queue_worker.start()

    logger.info("FastAPI microservice startup complete. Worker actively listening for queue events.")

    yield

    # Shutdown sequence
    logger.info("Shutting down CleanDesk microservice...")
    await queue_worker.stop()
    await queue_service.disconnect()
    await db_manager.disconnect()
    logger.info("Shutdown cleanly finalized.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Microservice-based Event-Driven Messaging Pipeline ingesting simulated Instagram "
        "and Shopify webhooks, processing via an async Redis queue with rate-limiting "
        "and account protection, enriching via RAG & Gemini AI, and broadcasting to a Universal Inbox."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend and external integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root info endpoint."""
    return {
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_STR,
        "websocket_endpoint": "/ws/inbox"
    }


@app.websocket("/ws/inbox")
@app.websocket("/api/ws")
async def websocket_inbox_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time live inbox updates and chat status pushes."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep socket alive and accept ping/commands from client if any
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client terminated: {e}")
        ws_manager.disconnect(websocket)
