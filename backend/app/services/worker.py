"""Asynchronous Message Queue Consumer & Event Worker

Processes incoming queued webhook interactions asynchronously.
Orchestrates:
1. Account health & rate-limit validation (daily limits, risk scoring).
2. Human-like inter-message pacing.
3. RAG context retrieval and Gemini AI brand reply generation.
4. Terminal status updates in MongoDB.
5. Real-time WebSocket event emission to connected frontend inboxes.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional
from app.core.logging import logger
from app.db.session import db_manager
from app.models.interaction import InteractionStatus
from app.services.queue_service import queue_service
from app.services.rate_limiter import rate_limiter
from app.services.rag_service import rag_service
from app.api.websockets.manager import ws_manager


class QueueWorker:
    def __init__(self):
        self._is_running = False
        self._worker_task: Optional[asyncio.Task] = None

    def start(self):
        """Starts the background worker task."""
        if not self._is_running:
            self._is_running = True
            self._worker_task = asyncio.create_task(self._run_loop())
            logger.info("Background Queue Consumer Worker started.")

    async def stop(self):
        """Stops the background worker gracefully."""
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Background Queue Consumer Worker stopped.")

    async def _run_loop(self):
        """Main worker dequeue and process loop."""
        while self._is_running:
            try:
                item = await queue_service.dequeue(timeout_seconds=0.5)
                if item:
                    await self.process_interaction(item)
                else:
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in queue consumer loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    async def process_interaction(self, item: dict):
        """Processes a single dequeued interaction through the safety & AI pipeline."""
        interaction_id = item.get("interaction_id")
        account_id = item.get("account_id")
        interactions_col = db_manager.get_collection("interactions")
        accounts_col = db_manager.get_collection("accounts")

        interaction = await interactions_col.find_one({"_id": interaction_id})
        if not interaction:
            interaction = await interactions_col.find_one({"id": interaction_id})

        if not interaction:
            logger.warning(f"Interaction {interaction_id} not found in database. Skipping.")
            return

        # 1. Transition status to PROCESSING and broadcast
        await interactions_col.update_one(
            {"_id": interaction["_id"]},
            {"$set": {"status": InteractionStatus.PROCESSING, "updated_at": datetime.now(timezone.utc)}}
        )
        interaction["status"] = InteractionStatus.PROCESSING
        await ws_manager.broadcast("INTERACTION_PROCESSING", interaction)

        message_body = interaction.get("message_body", "")
        platform = interaction.get("platform", "INSTAGRAM")
        sender_name = interaction.get("sender_name", "Valued Customer")

        # 2. Analyze Sentiment and Inbound Risk
        sentiment, risk_delta, risk_flag, risk_reason = rate_limiter.analyze_sentiment_and_risk(message_body)

        # 3. Content Safety & Threat Gate:
        # If inbound message is flagged as high-risk, a threat, or abusive, halt automated AI response
        # to protect brand reputation and prevent bot responses to hostile/dangerous content.
        if risk_flag:
            block_reason = f"Safety Shield: Automated reply blocked ({risk_reason}). Held for human review."
            logger.warning(f"Interaction {interaction_id} held: {block_reason}")
            await rate_limiter.record_risk_escalation(account_id, risk_delta=risk_delta)

            new_score = min(100, interaction.get("risk_score", 10) + risk_delta)
            await interactions_col.update_one(
                {"_id": interaction["_id"]},
                {
                    "$set": {
                        "status": InteractionStatus.FAILED,
                        "sentiment": sentiment,
                        "risk_flag": True,
                        "risk_score": new_score,
                        "risk_reason": block_reason,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            interaction["status"] = InteractionStatus.FAILED
            interaction["sentiment"] = sentiment
            interaction["risk_flag"] = True
            interaction["risk_score"] = new_score
            interaction["risk_reason"] = block_reason

            await ws_manager.broadcast("INTERACTION_FAILED", interaction)

            # Broadcast updated account health
            acc_fresh = await accounts_col.find_one({"_id": account_id}) or await accounts_col.find_one({"id": account_id})
            if acc_fresh:
                await ws_manager.broadcast("ACCOUNT_UPDATED", acc_fresh)
            return

        # 4. Evaluate Account Health & Rate Limits
        is_healthy, health_msg, account_doc = await rate_limiter.evaluate_account_health(account_id)

        if not is_healthy:
            # Blocked by Rate Limiter / Account Health Protection
            logger.warning(f"Interaction {interaction_id} blocked: {health_msg}")
            await interactions_col.update_one(
                {"_id": interaction["_id"]},
                {
                    "$set": {
                        "status": InteractionStatus.FAILED,
                        "sentiment": sentiment,
                        "risk_flag": True,
                        "risk_reason": health_msg,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            interaction["status"] = InteractionStatus.FAILED
            interaction["risk_flag"] = True
            interaction["risk_reason"] = health_msg
            await ws_manager.broadcast("INTERACTION_FAILED", interaction)

            # Broadcast updated account health
            if account_doc:
                acc_fresh = await accounts_col.find_one({"_id": account_doc["_id"]})
                if acc_fresh:
                    await ws_manager.broadcast("ACCOUNT_UPDATED", acc_fresh)
            return

        # 5. Enforce Inter-Message Pacing
        await rate_limiter.enforce_pacing(account_id, account_doc)

        # 6. Generate AI Response via RAG
        logger.info(f"Generating brand AI reply for {platform} interaction: '{message_body[:40]}...'")
        ai_result = await rag_service.generate_reply(
            query=message_body,
            platform=platform,
            customer_name=sender_name,
            account_id=account_id
        )

        ai_reply = ai_result.get("reply", "")
        rag_sources = ai_result.get("sources", [])

        # 6. Update Successful Dispatch in MongoDB and Account Stats
        await rate_limiter.record_successful_dispatch(account_id, risk_delta=risk_delta)

        await interactions_col.update_one(
            {"_id": interaction["_id"]},
            {
                "$set": {
                    "status": InteractionStatus.SENT,
                    "sentiment": sentiment,
                    "risk_flag": risk_flag,
                    "risk_reason": risk_reason,
                    "ai_reply": ai_reply,
                    "rag_sources": rag_sources,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        interaction["status"] = InteractionStatus.SENT
        interaction["sentiment"] = sentiment
        interaction["risk_flag"] = risk_flag
        interaction["risk_reason"] = risk_reason
        interaction["ai_reply"] = ai_reply
        interaction["rag_sources"] = rag_sources

        logger.info(f"Interaction {interaction_id} enriched and dispatched successfully.")

        # 7. Broadcast Live Events to Connected Dashboards
        await ws_manager.broadcast("INTERACTION_COMPLETED", interaction)
        acc_updated = await accounts_col.find_one({"_id": account_doc["_id"]})
        if acc_updated:
            await ws_manager.broadcast("ACCOUNT_UPDATED", acc_updated)


# Singleton Worker Instance
queue_worker = QueueWorker()
