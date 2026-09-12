"""Redis Event Queue Service

Implements an asynchronous message queue using Redis (rpush/blpop)
for decoupled, asynchronous webhook processing and rate-limited dispatch.
Includes a resilient fallback to an in-memory async queue when a live
Redis daemon is not running.
"""

import asyncio
import json
from typing import Any, Dict, Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger


class QueueService:
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.is_connected_to_real_redis: bool = False
        self._memory_queue: asyncio.Queue = asyncio.Queue()
        self.queue_name = settings.REDIS_QUEUE_NAME
        self.dlq_name = settings.REDIS_DLQ_NAME

    async def connect(self):
        """Initializes connection to Redis (including cloud providers like Upstash) with failover fallback."""
        raw_url = (settings.REDIS_URL or "").strip()
        token = (settings.REDIS_TOKEN or settings.UPSTASH_REDIS_REST_TOKEN or "").strip()

        # Handle Upstash HTTPS REST URL format: https://fit-thrush-109841.upstash.io
        if raw_url.startswith("https://") or raw_url.startswith("http://"):
            clean_host = raw_url.replace("https://", "").replace("http://", "").rstrip("/")
            if token:
                url = f"rediss://default:{token}@{clean_host}:6379"
                logger.info(f"Normalized Upstash REST URL + Token to TLS Redis endpoint for {clean_host}")
            else:
                logger.warning(
                    f"Upstash HTTPS URL detected ({clean_host}), but REDIS_TOKEN is empty in .env. "
                    "Please paste your Upstash token as REDIS_TOKEN in backend/.env. Falling back to memory queue."
                )
                self.is_connected_to_real_redis = False
                self.redis_client = None
                return
        elif raw_url:
            url = raw_url
            # If user provided a rediss:// URL without password but specified REDIS_TOKEN
            if token and "@" not in url:
                prefix = "rediss://" if url.startswith("rediss://") else "redis://"
                host_part = url.replace(prefix, "")
                url = f"{prefix}default:{token}@{host_part}"
        else:
            url = "redis://localhost:6379/0"

        safe_url = url.split("@")[-1] if "@" in url else url

        try:
            extra_kwargs = {
                "encoding": "utf-8",
                "decode_responses": True,
                "socket_timeout": 5.0,
                "socket_connect_timeout": 5.0,
            }
            if url.startswith("rediss://"):
                extra_kwargs["ssl_cert_reqs"] = None

            client = aioredis.from_url(url, **extra_kwargs)
            await asyncio.wait_for(client.ping(), timeout=5.0)
            self.redis_client = client
            self.is_connected_to_real_redis = True
            logger.info(f"Connected to Redis message queue at {safe_url}")
        except Exception as e:
            self.is_connected_to_real_redis = False
            self.redis_client = None
            logger.warning(
                f"Redis server connection to {safe_url} failed ({e}). "
                "Falling back to high-performance async in-memory event queue."
            )

    async def disconnect(self):
        """Closes Redis connection cleanly."""
        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Closed Redis connection.")

    async def enqueue(self, payload: Dict[str, Any]) -> bool:
        """Pushes an event payload onto the queue."""
        serialized = json.dumps(payload, default=str)
        if self.is_connected_to_real_redis and self.redis_client:
            try:
                await self.redis_client.rpush(self.queue_name, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis enqueue failed ({e}), falling back to memory queue.")
        
        await self._memory_queue.put(serialized)
        return True

    async def dequeue(self, timeout_seconds: float = 1.0) -> Optional[Dict[str, Any]]:
        """Pops an event payload from the queue (blocking with timeout)."""
        if self.is_connected_to_real_redis and self.redis_client:
            try:
                # blpop returns tuple (queue_name, item)
                res = await self.redis_client.blpop(self.queue_name, timeout=int(timeout_seconds) or 1)
                if res:
                    _, raw_data = res
                    return json.loads(raw_data)
                return None
            except Exception as e:
                logger.error(f"Redis dequeue failed ({e}), checking memory queue.")

        # Check in-memory queue with timeout
        try:
            raw_data = await asyncio.wait_for(self._memory_queue.get(), timeout=timeout_seconds)
            self._memory_queue.task_done()
            return json.loads(raw_data)
        except asyncio.TimeoutError:
            return None

    async def send_to_dlq(self, payload: Dict[str, Any], reason: str):
        """Moves an unprocessable or permanently failed item to the Dead Letter Queue."""
        payload["dlq_reason"] = reason
        serialized = json.dumps(payload, default=str)
        if self.is_connected_to_real_redis and self.redis_client:
            try:
                await self.redis_client.rpush(self.dlq_name, serialized)
                return
            except Exception as e:
                logger.error(f"Failed pushing to Redis DLQ: {e}")
        logger.warning(f"Item sent to DLQ: {payload.get('interaction_id')}, reason: {reason}")

    async def get_queue_size(self) -> int:
        """Returns the current number of pending items in the queue."""
        if self.is_connected_to_real_redis and self.redis_client:
            try:
                return await self.redis_client.llen(self.queue_name)
            except Exception:
                pass
        return self._memory_queue.qsize()


# Singleton Queue Instance
queue_service = QueueService()
