"""Reset DB and Redis Script

Clears all test interactions from MongoDB and Upstash Redis, resets
account quotas and health scores, and leaves clean seed data ready
for fresh end-to-end testing.
"""

import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.db.session import db_manager
from app.db.init_db import seed_database
from app.services.queue_service import queue_service


async def reset_environment():
    print("==================================================")
    print("🧹 CleanDesk: Resetting Database & Redis State...")
    print("==================================================")

    # 1. Connect MongoDB
    await db_manager.connect()
    interactions_col = db_manager.get_collection("interactions")
    accounts_col = db_manager.get_collection("accounts")

    # Clear interactions
    del_result = await interactions_col.delete_many({})
    print(f"✅ Cleared MongoDB 'interactions' collection: {del_result.deleted_count} documents removed.")

    # Reset accounts to clean healthy state
    await accounts_col.update_many(
        {},
        {
            "$set": {
                "sent_today": 0,
                "risk_score": 10,
                "health_status": "HEALTHY",
                "last_sent_at": None,
            }
        },
    )
    print("✅ Reset MongoDB 'accounts' collection: sent_today=0, risk_score=10, health_status=HEALTHY.")

    # Re-verify seed data
    await seed_database()
    print("✅ Re-seeded default knowledge base documents and accounts.")

    # 2. Connect Redis and purge queue
    await queue_service.connect()
    if queue_service.redis_client:
        try:
            # Delete the interaction queue
            await queue_service.redis_client.delete(queue_service.queue_name)
            await queue_service.redis_client.delete(queue_service.dlq_name)
            print(f"✅ Purged Redis queues: '{queue_service.queue_name}' & '{queue_service.dlq_name}'.")

            # Delete any pacing keys
            keys = await queue_service.redis_client.keys("account:*:pacing")
            if keys:
                await queue_service.redis_client.delete(*keys)
                print(f"✅ Removed {len(keys)} pacing locks from Redis.")
        except Exception as e:
            print(f"⚠️ Warning while flushing Redis: {e}")
    else:
        print("ℹ️ Redis running in-memory mode, queue cleared.")

    await queue_service.disconnect()
    await db_manager.disconnect()

    print("==================================================")
    print("✨ System reset complete! Ready for fresh testing.")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(reset_environment())
