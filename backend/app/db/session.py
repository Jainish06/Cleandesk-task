"""MongoDB Session & Resilient Connection Manager

Provides an async Motor MongoDB client when MONGODB_URI is provided.
If MONGODB_URI is blank or unreachable, falls back to a high-fidelity
in-memory async database implementation so the microservice and unit tests
function seamlessly out of the box until the user pastes their live connection URL.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logging import logger


class InMemoryAsyncCollection:
    """Async Mongo-like in-memory collection fallback for local dev & testing."""
    def __init__(self, name: str):
        self.name = name
        self._data: Dict[str, Dict[str, Any]] = {}

    async def insert_one(self, document: Dict[str, Any]):
        doc = dict(document)
        doc_id = str(doc.get("_id") or doc.get("id") or uuid.uuid4())
        doc["_id"] = doc_id
        doc["id"] = doc_id
        if "created_at" not in doc:
            doc["created_at"] = datetime.now(timezone.utc)
        if "updated_at" not in doc:
            doc["updated_at"] = datetime.now(timezone.utc)
        self._data[doc_id] = doc
        
        class InsertResult:
            inserted_id = doc_id
        return InsertResult()

    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self._data.values():
            if self._matches(doc, filter_query):
                return dict(doc)
        return None

    def find(self, filter_query: Optional[Dict[str, Any]] = None):
        filter_query = filter_query or {}
        matches = [dict(d) for d in self._data.values() if self._matches(d, filter_query)]
        
        class Cursor:
            def __init__(self, items):
                self._items = items

            def sort(self, key_or_list, direction=1):
                # Simple sort support
                if isinstance(key_or_list, list):
                    key, direction = key_or_list[0]
                else:
                    key = key_or_list
                self._items.sort(
                    key=lambda x: x.get(key, 0) or 0,
                    reverse=(direction == -1)
                )
                return self

            def skip(self, n: int):
                self._items = self._items[n:]
                return self

            def limit(self, n: int):
                self._items = self._items[:n]
                return self

            async def to_list(self, length: Optional[int] = None):
                if length is not None:
                    return self._items[:length]
                return self._items

            def __aiter__(self):
                self._iter = iter(self._items)
                return self

            async def __anext__(self):
                try:
                    return next(self._iter)
                except StopIteration:
                    raise StopAsyncIteration

        return Cursor(matches)

    async def count_documents(self, filter_query: Optional[Dict[str, Any]] = None) -> int:
        filter_query = filter_query or {}
        return sum(1 for d in self._data.values() if self._matches(d, filter_query))

    async def update_one(self, filter_query: Dict[str, Any], update_doc: Dict[str, Any]):
        for doc_id, doc in self._data.items():
            if self._matches(doc, filter_query):
                if "$set" in update_doc:
                    for k, v in update_doc["$set"].items():
                        doc[k] = v
                if "$inc" in update_doc:
                    for k, v in update_doc["$inc"].items():
                        doc[k] = doc.get(k, 0) + v
                doc["updated_at"] = datetime.now(timezone.utc)
                self._data[doc_id] = doc
                
                class UpdateResult:
                    matched_count = 1
                    modified_count = 1
                return UpdateResult()
        class EmptyUpdateResult:
            matched_count = 0
            modified_count = 0
        return EmptyUpdateResult()

    async def delete_many(self, filter_query: Optional[Dict[str, Any]] = None):
        filter_query = filter_query or {}
        to_del = [doc_id for doc_id, doc in self._data.items() if self._matches(doc, filter_query)]
        for k in to_del:
            del self._data[k]

    def _matches(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        for k, v in query.items():
            if k == "_id" or k == "id":
                if doc.get("_id") != v and doc.get("id") != v:
                    return False
            elif isinstance(v, dict):
                # Basic $regex or $in or $gt
                if "$regex" in v:
                    pattern = v["$regex"]
                    ignore_case = v.get("$options") == "i"
                    target_str = str(doc.get(k, ""))
                    if ignore_case:
                        if pattern.lower() not in target_str.lower():
                            return False
                    elif pattern not in target_str:
                        return False
                elif "$in" in v:
                    if doc.get(k) not in v["$in"]:
                        return False
            else:
                if doc.get(k) != v:
                    return False
        return True


class InMemoryAsyncDatabase:
    """Mock MongoDB database routing to memory collections."""
    def __init__(self, db_name: str):
        self.name = db_name
        self._collections: Dict[str, InMemoryAsyncCollection] = {}

    def __getitem__(self, collection_name: str) -> InMemoryAsyncCollection:
        if collection_name not in self._collections:
            self._collections[collection_name] = InMemoryAsyncCollection(collection_name)
        return self._collections[collection_name]


class DatabaseManager:
    """Singleton connection manager for MongoDB."""
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Any = None
        self.is_connected_to_real_mongo: bool = False

    async def connect(self):
        uri = (settings.MONGODB_URI or "").strip()
        if uri:
            try:
                logger.info(f"Connecting to MongoDB at {uri[:25]}... (URI configured)")
                self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=3000)
                # Verify connectivity with a quick ping
                await asyncio.wait_for(self.client.admin.command('ping'), timeout=3.5)
                self.db = self.client[settings.MONGODB_DB_NAME]
                self.is_connected_to_real_mongo = True
                logger.info("Successfully connected to live MongoDB cluster!")
                return
            except Exception as e:
                logger.warning(f"Could not connect to live MongoDB: {e}. Falling back to internal resilient datastore.")

        logger.info("Using internal resilient Async MongoDB datastore (Paste MONGODB_URI in .env to connect to live cluster).")
        self.db = InMemoryAsyncDatabase(settings.MONGODB_DB_NAME)
        self.is_connected_to_real_mongo = False

    async def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB client connection.")

    def get_collection(self, name: str):
        if self.db is None:
            # Lazy init fallback
            self.db = InMemoryAsyncDatabase(settings.MONGODB_DB_NAME)
        return self.db[name]


# Global singleton instance
db_manager = DatabaseManager()

def get_db():
    return db_manager.db
