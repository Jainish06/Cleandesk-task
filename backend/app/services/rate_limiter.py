"""Rate Limiting & Account Health Protection Engine

Enforces multi-tier safety policies to protect social media and e-commerce accounts
from automated spam bans, platform API throttling, and high-risk compliance violations.

Tiers:
1. Daily Quota Throttling (sent_today vs daily_limit)
2. Risk Score Gatekeeping (Account risk score 0-100, threshold rejection at >= 80)
3. Inter-Message Pacing (Minimum delay between actions per account)
4. Sentiment & Risk Flagging (Keyword heuristics for chargebacks, disputes, scams)
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from app.db.session import db_manager
from app.models.account import AccountHealthStatus
from app.models.interaction import SentimentEnum
from app.core.config import settings
from app.core.logging import logger

THREAT_AND_VIOLENCE_KEYWORDS = [
    "kill", "death", "murder", "threat", "thereat", "threaten", "thereaten",
    "die", "suicide", "bomb", "violence", "violent", "harm", "attack",
    "assault", "shoot", "shooting", "weapon", "gun", "knife", "terror",
    "terrorist", "terrorism", "hostage", "abuse", "abusive", "harass",
    "harassment", "stalk", "stalking", "hurt you", "kill you"
]

HIGH_RISK_KEYWORDS = [
    "chargeback", "fraud", "scam", "scammer", "lawyer", "attorney", "sue",
    "suing", "court", "police", "cop", "cops", "fbi", "stolen", "report you",
    "fake products", "counterfeit", "bbb", "better business bureau",
    "trading standards", "legal action", "dispute"
]

NEGATIVE_KEYWORDS = [
    "terrible", "horrible", "worst", "disgusting", "trash", "garbage",
    "ripoff", "rip off", "cheat", "cheated", "liar", "thief", "stole",
    "hate you", "hate this", "fuck", "shit", "bullshit", "bitch", "bastard"
]

URGENT_KEYWORDS = [
    "urgent", "asap", "immediately", "broken", "emergency", "damaged",
    "cancelled", "wrong address", "stop order"
]

POSITIVE_KEYWORDS = [
    "love", "amazing", "great", "thanks", "thank you", "awesome",
    "perfect", "excellent", "happy", "best", "pleased", "fantastic"
]


class RateLimiterService:
    def __init__(self):
        # In-memory lock per account to guarantee sequential inter-message pacing
        self._account_locks: Dict[str, asyncio.Lock] = {}

    def _get_account_lock(self, account_id: str) -> asyncio.Lock:
        if account_id not in self._account_locks:
            self._account_locks[account_id] = asyncio.Lock()
        return self._account_locks[account_id]

    def analyze_sentiment_and_risk(self, message: str) -> Tuple[SentimentEnum, int, bool, Optional[str]]:
        """Analyzes incoming message for sentiment, risk elevation, and safety flags."""
        lower_msg = message.lower()
        risk_increment = 0
        risk_flag = False
        risk_reason = None
        sentiment = SentimentEnum.NEUTRAL

        # Check 1: Physical Threat / Violence / Dangerous Content
        matched_threat = [kw for kw in THREAT_AND_VIOLENCE_KEYWORDS if kw in lower_msg]
        if matched_threat:
            risk_increment = 40
            risk_flag = True
            risk_reason = f"Safety & Threat Violation detected: '{matched_threat[0]}'"
            sentiment = SentimentEnum.NEGATIVE
            return sentiment, risk_increment, risk_flag, risk_reason

        # Check 2: High Risk / Legal / Chargeback triggers
        matched_risk = [kw for kw in HIGH_RISK_KEYWORDS if kw in lower_msg]
        if matched_risk:
            risk_increment = 25
            risk_flag = True
            risk_reason = f"High-risk compliance keywords detected: '{matched_risk[0]}'"
            sentiment = SentimentEnum.NEGATIVE
            return sentiment, risk_increment, risk_flag, risk_reason

        # Check 3: Hostility / Negative Sentiment / Profanity
        matched_neg = [kw for kw in NEGATIVE_KEYWORDS if kw in lower_msg]
        if matched_neg:
            sentiment = SentimentEnum.NEGATIVE
            risk_increment = 15
            risk_flag = True
            risk_reason = f"Abusive/hostile language detected: '{matched_neg[0]}'"
            return sentiment, risk_increment, risk_flag, risk_reason

        # Check 4: Urgency
        if any(kw in lower_msg for kw in URGENT_KEYWORDS):
            sentiment = SentimentEnum.URGENT
            risk_increment = 5

        # Check 5: Positive Sentiment
        elif any(kw in lower_msg for kw in POSITIVE_KEYWORDS):
            sentiment = SentimentEnum.POSITIVE
            risk_increment = -2  # Good interactions reduce account risk slightly

        return sentiment, risk_increment, risk_flag, risk_reason

    async def evaluate_account_health(self, account_id: str) -> Tuple[bool, str, Optional[dict]]:
        """Evaluates whether an account is eligible to send a message or is throttled/restricted."""
        accounts_col = db_manager.get_collection("accounts")
        account = await accounts_col.find_one({"_id": account_id})
        if not account:
            # Check by alias id
            account = await accounts_col.find_one({"id": account_id})

        if not account:
            return False, f"Account '{account_id}' not found in registry.", None

        # Check 1: Daily Quota Limit
        daily_limit = account.get("daily_limit", settings.MAX_DAILY_QUOTA_DEFAULT)
        sent_today = account.get("sent_today", 0)
        if sent_today >= daily_limit:
            return False, f"Daily dispatch limit reached ({sent_today}/{daily_limit}). Throttled to prevent ban.", account

        # Check 2: Risk Score Rejection
        risk_score = account.get("risk_score", 0)
        if risk_score >= settings.RISK_THRESHOLD_REJECTION:
            return False, f"Account risk score ({risk_score}/100) exceeds safety threshold ({settings.RISK_THRESHOLD_REJECTION}). Account placed in RESTRICTED state.", account

        return True, "Account healthy and within rate limits.", account

    async def enforce_pacing(self, account_id: str, account_doc: dict):
        """Enforces minimum inter-message delay (pacing) to mimic natural human behavior."""
        async with self._get_account_lock(account_id):
            last_sent_at = account_doc.get("last_sent_at")
            if last_sent_at:
                if isinstance(last_sent_at, str):
                    try:
                        last_sent_at = datetime.fromisoformat(last_sent_at)
                    except Exception:
                        last_sent_at = None

            if last_sent_at:
                now = datetime.now(timezone.utc)
                if last_sent_at.tzinfo is None:
                    last_sent_at = last_sent_at.replace(tzinfo=timezone.utc)
                elapsed_ms = (now - last_sent_at).total_seconds() * 1000
                required_delay_ms = settings.INTER_MESSAGE_PACING_MS

                if elapsed_ms < required_delay_ms:
                    wait_time = (required_delay_ms - elapsed_ms) / 1000.0
                    logger.info(f"Pacing account {account_id}: sleeping {wait_time:.3f}s to avoid bot detection.")
                    await asyncio.sleep(wait_time)

    async def record_successful_dispatch(self, account_id: str, risk_delta: int = 0):
        """Increments sent_today count, updates last_sent_at, and adjusts risk score."""
        accounts_col = db_manager.get_collection("accounts")
        account = await accounts_col.find_one({"_id": account_id}) or await accounts_col.find_one({"id": account_id})
        
        new_risk = 10
        if account:
            current_risk = account.get("risk_score", 10)
            new_risk = max(0, min(100, current_risk + risk_delta))
            new_status = AccountHealthStatus.HEALTHY
            if new_risk >= settings.RISK_THRESHOLD_REJECTION:
                new_status = AccountHealthStatus.RESTRICTED
            elif new_risk >= 50:
                new_status = AccountHealthStatus.WARNING

            await accounts_col.update_one(
                {"_id": account["_id"]},
                {
                    "$inc": {"sent_today": 1},
                    "$set": {
                        "risk_score": new_risk,
                        "health_status": new_status,
                        "last_sent_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

    async def record_risk_escalation(self, account_id: str, risk_delta: int = 25):
        """Escalates account risk score when a high-risk/threat interaction is received without incrementing sent quota."""
        accounts_col = db_manager.get_collection("accounts")
        account = await accounts_col.find_one({"_id": account_id}) or await accounts_col.find_one({"id": account_id})
        if account:
            current_risk = account.get("risk_score", 10)
            new_risk = max(0, min(100, current_risk + risk_delta))
            new_status = AccountHealthStatus.HEALTHY
            if new_risk >= settings.RISK_THRESHOLD_REJECTION:
                new_status = AccountHealthStatus.RESTRICTED
            elif new_risk >= 50:
                new_status = AccountHealthStatus.WARNING

            await accounts_col.update_one(
                {"_id": account["_id"]},
                {
                    "$set": {
                        "risk_score": new_risk,
                        "health_status": new_status,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )


# Singleton Rate Limiter
rate_limiter = RateLimiterService()
