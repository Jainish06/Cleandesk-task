"""Pytest Configuration and Test Fixtures"""

import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.db.session import db_manager
from app.db.init_db import seed_database
from app.services.queue_service import queue_service


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def initialize_test_environment():
    """Initializes DB, seeds defaults, and resets collections before each test."""
    await db_manager.connect()
    await seed_database()
    await queue_service.connect()
    yield
    # Clean up
    await queue_service.disconnect()
    await db_manager.disconnect()


@pytest_asyncio.fixture
async def client():
    """Provides an AsyncClient for testing the FastAPI ASGI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
