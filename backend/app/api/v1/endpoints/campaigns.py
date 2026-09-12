"""Campaign Dispatch Endpoints

Handles bulk outbound messaging campaigns (e.g. VIP promotions, restock alerts)
with asynchronous queuing, account quota preservation, and automatic pacing.
"""

import asyncio
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from app.core.logging import logger
from app.db.session import db_manager
from app.models.interaction import InteractionStatus, InteractionType, SentimentEnum
from app.schemas.campaign import CampaignDispatchRequest, CampaignDispatchResponse
from app.services.queue_service import queue_service
from app.api.websockets.manager import ws_manager

router = APIRouter()


async def execute_bulk_queueing(
    campaign_id: str,
    account_id: str,
    platform: str,
    recipients: list,
    template_message: str,
    pacing_delay_ms: int
):
    """Background task to gradually enqueue campaign messages into Redis to avoid pipeline spikes."""
    interactions_col = db_manager.get_collection("interactions")
    logger.info(f"Starting bulk queueing for campaign {campaign_id}: {len(recipients)} recipients")

    for idx, recipient in enumerate(recipients):
        interaction_id = f"cmp_{uuid.uuid4().hex[:12]}"
        
        # Personalize message if template has placeholder
        personalized = recipient.custom_message or template_message.replace("{name}", recipient.recipient_name)

        doc = {
            "_id": interaction_id,
            "id": interaction_id,
            "account_id": account_id,
            "platform": platform,
            "sender_id": recipient.recipient_id,
            "sender_name": recipient.recipient_name,
            "message_body": personalized,
            "interaction_type": InteractionType.CAMPAIGN,
            "status": InteractionStatus.QUEUED,
            "sentiment": SentimentEnum.POSITIVE,
            "risk_score": 10,
            "risk_flag": False,
            "risk_reason": None,
            "ai_reply": None,
            "rag_sources": [],
            "campaign_id": campaign_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        await interactions_col.insert_one(doc)
        await queue_service.enqueue({
            "interaction_id": interaction_id,
            "account_id": account_id,
            "platform": platform,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        await ws_manager.broadcast("INTERACTION_CREATED", doc)

        # Micro-pause between queue injections
        if pacing_delay_ms > 0:
            await asyncio.sleep(pacing_delay_ms / 1000.0)

    logger.info(f"Campaign {campaign_id} successfully queued all {len(recipients)} interactions.")


@router.post("/dispatch", response_model=CampaignDispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def dispatch_campaign(
    payload: CampaignDispatchRequest,
    background_tasks: BackgroundTasks
):
    """Dispatches a bulk messaging campaign asynchronously via background task and Redis queue."""
    campaign_id = f"camp_{uuid.uuid4().hex[:8]}"
    total = len(payload.recipients)

    # Verify account exists
    accounts_col = db_manager.get_collection("accounts")
    account = await accounts_col.find_one({"_id": payload.account_id}) or await accounts_col.find_one({"id": payload.account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{payload.account_id}' does not exist."
        )

    # Check available quota
    daily_limit = account.get("daily_limit", 50)
    sent_today = account.get("sent_today", 0)
    remaining = max(0, daily_limit - sent_today)

    if remaining < total:
        logger.warning(f"Campaign requested {total} messages but account only has {remaining} quota remaining.")

    pacing_ms = payload.pacing_delay_ms or 500
    estimated_duration = (total * pacing_ms) / 1000.0

    # Launch background task for graceful paced queueing
    background_tasks.add_task(
        execute_bulk_queueing,
        campaign_id=campaign_id,
        account_id=payload.account_id,
        platform=payload.platform,
        recipients=payload.recipients,
        template_message=payload.template_message,
        pacing_delay_ms=pacing_ms
    )

    return CampaignDispatchResponse(
        campaign_id=campaign_id,
        status="QUEUED",
        total_queued=total,
        account_id=payload.account_id,
        estimated_duration_seconds=estimated_duration,
        message=f"Campaign '{payload.campaign_name}' scheduled. {total} messages dispatched to async queue."
    )
