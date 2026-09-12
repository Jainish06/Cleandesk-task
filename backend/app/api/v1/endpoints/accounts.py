"""Account Health & Platform Configuration Endpoints

Provides visibility into Instagram & Shopify account health metrics,
sent message counters, risk scores, and controls to adjust or reset quotas for testing.
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.db.session import db_manager
from app.schemas.account import AccountResponse, AccountUpdateRequest
from app.api.websockets.manager import ws_manager

router = APIRouter()


@router.get("", response_model=List[AccountResponse])
async def list_accounts():
    """Lists all registered Instagram and Shopify accounts with live health status."""
    accounts_col = db_manager.get_collection("accounts")
    docs = await accounts_col.find({}).to_list(length=50)

    res = []
    for d in docs:
        res.append(AccountResponse(
            id=str(d.get("_id") or d.get("id")),
            platform=d.get("platform", "INSTAGRAM"),
            handle=d.get("handle", "@account"),
            name=d.get("name", "Store"),
            daily_limit=d.get("daily_limit", 50),
            sent_today=d.get("sent_today", 0),
            risk_score=d.get("risk_score", 10),
            health_status=d.get("health_status", "HEALTHY"),
            last_sent_at=d.get("last_sent_at"),
            created_at=d.get("created_at") or datetime.now(timezone.utc),
            updated_at=d.get("updated_at") or datetime.now(timezone.utc)
        ))
    return res


@router.post("/{account_id}/reset", response_model=AccountResponse)
async def reset_account_metrics(account_id: str):
    """Resets sent_today counters and risk_score back to safe healthy state for demonstration."""
    accounts_col = db_manager.get_collection("accounts")
    account = await accounts_col.find_one({"_id": account_id}) or await accounts_col.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    updates = {
        "sent_today": 0,
        "risk_score": 10,
        "health_status": "HEALTHY",
        "updated_at": datetime.now(timezone.utc)
    }

    await accounts_col.update_one({"_id": account["_id"]}, {"$set": updates})
    account.update(updates)
    account["id"] = str(account.get("_id") or account.get("id"))

    # Broadcast updated state over WebSockets
    await ws_manager.broadcast("ACCOUNT_UPDATED", account)

    return AccountResponse(
        id=account["id"],
        platform=account.get("platform", "INSTAGRAM"),
        handle=account.get("handle", ""),
        name=account.get("name", ""),
        daily_limit=account.get("daily_limit", 50),
        sent_today=account["sent_today"],
        risk_score=account["risk_score"],
        health_status=account["health_status"],
        last_sent_at=account.get("last_sent_at"),
        created_at=account.get("created_at") or datetime.now(timezone.utc),
        updated_at=account.get("updated_at") or datetime.now(timezone.utc)
    )


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(account_id: str, updates: AccountUpdateRequest):
    """Updates account risk limits or thresholds."""
    accounts_col = db_manager.get_collection("accounts")
    account = await accounts_col.find_one({"_id": account_id}) or await accounts_col.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    fields_to_set = {"updated_at": datetime.now(timezone.utc)}
    if updates.daily_limit is not None:
        fields_to_set["daily_limit"] = updates.daily_limit
    if updates.risk_score is not None:
        fields_to_set["risk_score"] = updates.risk_score
    if updates.health_status is not None:
        fields_to_set["health_status"] = updates.health_status

    await accounts_col.update_one({"_id": account["_id"]}, {"$set": fields_to_set})
    account.update(fields_to_set)
    account["id"] = str(account.get("_id") or account.get("id"))

    await ws_manager.broadcast("ACCOUNT_UPDATED", account)

    return AccountResponse(
        id=account["id"],
        platform=account.get("platform", "INSTAGRAM"),
        handle=account.get("handle", ""),
        name=account.get("name", ""),
        daily_limit=account.get("daily_limit", 50),
        sent_today=account.get("sent_today", 0),
        risk_score=account.get("risk_score", 10),
        health_status=account.get("health_status", "HEALTHY"),
        last_sent_at=account.get("last_sent_at"),
        created_at=account.get("created_at") or datetime.now(timezone.utc),
        updated_at=account.get("updated_at") or datetime.now(timezone.utc)
    )
