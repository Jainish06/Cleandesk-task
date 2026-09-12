"""Database Initialization & Seed Data

Seeds default connected accounts (Instagram & Shopify) and product knowledge base
documents to ensure a turnkey demo and testing experience.
"""

from datetime import datetime, timezone
from app.db.session import db_manager
from app.core.logging import logger

DEFAULT_ACCOUNTS = [
    {
        "_id": "acc_instagram_01",
        "id": "acc_instagram_01",
        "platform": "INSTAGRAM",
        "handle": "@cleandesk_shop",
        "name": "CleanDesk Lifestyle Official",
        "daily_limit": 50,
        "sent_today": 8,
        "risk_score": 15,
        "health_status": "HEALTHY",
        "last_sent_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "_id": "acc_shopify_01",
        "id": "acc_shopify_01",
        "platform": "SHOPIFY",
        "handle": "cleandesk-direct.myshopify.com",
        "name": "CleanDesk Direct Store",
        "daily_limit": 100,
        "sent_today": 12,
        "risk_score": 8,
        "health_status": "HEALTHY",
        "last_sent_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
]

DEFAULT_KNOWLEDGE = [
    {
        "_id": "kb_return_policy",
        "id": "kb_return_policy",
        "product_name": "Return & Refund Policy",
        "category": "POLICY",
        "context_text": (
            "We offer a 30-day hassle-free return window for all items in original condition. "
            "Domestic US return shipping is 100% free with our prepaid return label. "
            "Refunds are processed back to the original payment method within 3 to 5 business days after receipt."
        ),
        "created_at": datetime.now(timezone.utc)
    },
    {
        "_id": "kb_shipping_policy",
        "id": "kb_shipping_policy",
        "product_name": "Shipping & Delivery Times",
        "category": "POLICY",
        "context_text": (
            "Orders are dispatched within 24 hours. Standard domestic US shipping takes 3-5 business days (Free over $60). "
            "Priority Express shipping is available for $12 (1-2 business days). "
            "International shipping is available worldwide at a flat rate of $15 (7-12 business days). Tracking is emailed instantly."
        ),
        "created_at": datetime.now(timezone.utc)
    },
    {
        "_id": "kb_discount_faq",
        "id": "kb_discount_faq",
        "product_name": "Discounts & Promo Codes",
        "category": "DISCOUNT",
        "context_text": (
            "New customers can use discount code 'WELCOME15' at checkout for 15% off orders over $50. "
            "Students receive a 20% discount through StudentBeans. Only one coupon code may be applied per checkout."
        ),
        "created_at": datetime.now(timezone.utc)
    },
    {
        "_id": "kb_desk_mat",
        "id": "kb_desk_mat",
        "product_name": "CleanDesk Dual-Sided Vegan Leather Desk Mat",
        "category": "PRODUCT",
        "context_text": (
            "The CleanDesk Desk Mat retails for $49.99. Dimensions: 90cm x 40cm. "
            "Crafted from premium water-resistant vegan leather on one side and natural organic cork on the reverse. "
            "Easy to wipe clean with a damp cloth. Available in Midnight Black, Saddle Brown, and Slate Gray."
        ),
        "created_at": datetime.now(timezone.utc)
    },
    {
        "_id": "kb_cable_organizer",
        "id": "kb_cable_organizer",
        "product_name": "CleanDesk Magnetic Aluminum Cable Management Hub",
        "category": "PRODUCT",
        "context_text": (
            "Price: $29.99. Precision CNC-machined from space-grade anodized aluminum with neodymium magnets. "
            "Secures up to 5 charging cables (USB-C, Lightning, MagSafe, HDMI). Comes with a micro-suction reusable base that leaves no residue."
        ),
        "created_at": datetime.now(timezone.utc)
    },
    {
        "_id": "kb_gan_charger",
        "id": "kb_gan_charger",
        "product_name": "CleanDesk 65W GaN Dual USB-C Fast Wall Charger",
        "category": "PRODUCT",
        "context_text": (
            "Price: $39.99. GaN III semiconductor technology allows ultra-compact form factor with 2x USB-C Power Delivery ports and 1x USB-A port. "
            "Charges a MacBook Air from 0 to 50% in 30 minutes, or simultaneously fast-charges iPhone and iPad. Foldable US prongs with EU/UK travel adapters included."
        ),
        "created_at": datetime.now(timezone.utc)
    }
]

async def seed_database():
    """Seeds initial accounts and knowledge base documents if they don't exist."""
    accounts_col = db_manager.get_collection("accounts")
    knowledge_col = db_manager.get_collection("knowledge_base")

    # Seed Accounts
    for acc in DEFAULT_ACCOUNTS:
        existing = await accounts_col.find_one({"_id": acc["_id"]})
        if not existing:
            await accounts_col.insert_one(acc)
            logger.info(f"Seeded default account: {acc['name']} ({acc['platform']})")

    # Seed Knowledge Base
    for doc in DEFAULT_KNOWLEDGE:
        existing = await knowledge_col.find_one({"_id": doc["_id"]})
        if not existing:
            await knowledge_col.insert_one(doc)
            logger.info(f"Seeded knowledge base document: {doc['product_name']}")
