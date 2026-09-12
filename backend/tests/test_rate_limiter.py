"""Tests for Rate Limiting & Account Health Protection Engine"""

import pytest
from app.db.session import db_manager
from app.models.interaction import SentimentEnum
from app.services.rate_limiter import rate_limiter


@pytest.mark.asyncio
async def test_sentiment_and_high_risk_keyword_detection():
    """Verifies that high-risk dispute/legal keywords trigger risk flags and negative sentiment."""
    # Test 1: Chargeback threat
    hostile_msg = "I will contact my lawyer and file a chargeback with my bank immediately!"
    sentiment, risk_delta, risk_flag, risk_reason = rate_limiter.analyze_sentiment_and_risk(hostile_msg)

    assert risk_flag is True
    assert risk_delta >= 20
    assert sentiment == SentimentEnum.NEGATIVE
    assert "chargeback" in risk_reason.lower()

    # Test 1b: Physical safety and threat detection
    threat_msg_1 = "This is a kill threat"
    sentiment, risk_delta, risk_flag, risk_reason = rate_limiter.analyze_sentiment_and_risk(threat_msg_1)
    assert risk_flag is True
    assert risk_delta >= 30
    assert sentiment == SentimentEnum.NEGATIVE
    assert "safety" in risk_reason.lower() or "threat" in risk_reason.lower()

    threat_msg_2 = "this is a kill therea t"
    sentiment, risk_delta, risk_flag, risk_reason = rate_limiter.analyze_sentiment_and_risk(threat_msg_2)
    assert risk_flag is True
    assert sentiment == SentimentEnum.NEGATIVE

    # Test 2: Urgent order inquiry
    urgent_msg = "URGENT: I entered the wrong shipping address, please stop order ASAP!"
    sentiment, risk_delta, risk_flag, risk_reason = rate_limiter.analyze_sentiment_and_risk(urgent_msg)
    assert sentiment == SentimentEnum.URGENT

    # Test 3: Positive feedback
    positive_msg = "Love this desk mat so much, thank you for the fast shipping!"
    sentiment, risk_delta, risk_flag, risk_reason = rate_limiter.analyze_sentiment_and_risk(positive_msg)
    assert sentiment == SentimentEnum.POSITIVE


@pytest.mark.asyncio
async def test_daily_quota_exhaustion_throttling():
    """Verifies that exceeding the daily message quota blocks automated dispatch to prevent bans."""
    accounts_col = db_manager.get_collection("accounts")

    # Set account to daily limit capacity
    await accounts_col.update_one(
        {"_id": "acc_instagram_01"},
        {"$set": {"sent_today": 50, "daily_limit": 50}}
    )

    is_healthy, reason, account_doc = await rate_limiter.evaluate_account_health("acc_instagram_01")
    assert is_healthy is False
    assert "Daily dispatch limit reached" in reason


@pytest.mark.asyncio
async def test_risk_score_rejection():
    """Verifies that elevated risk scores (> 80) place the account in restricted state."""
    accounts_col = db_manager.get_collection("accounts")

    # Elevate risk score
    await accounts_col.update_one(
        {"_id": "acc_instagram_01"},
        {"$set": {"risk_score": 85, "sent_today": 5, "daily_limit": 50}}
    )

    is_healthy, reason, account_doc = await rate_limiter.evaluate_account_health("acc_instagram_01")
    assert is_healthy is False
    assert "safety threshold" in reason
