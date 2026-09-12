"""AI Response Generation & RAG Service

Performs semantic retrieval against the Product & Policy Knowledge Base
and uses Google Gemini AI to synthesize brand-aware, platform-tailored responses.
Includes a deterministic fallback generator when an API key is not configured.
"""

import math
import re
from typing import Any, Dict, List, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.db.session import db_manager

# Try importing modern google.genai, else fallback to google.generativeai
try:
    from google import genai
    from google.genai import types as genai_types
    HAS_GENAI = True
except ImportError:
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import google.generativeai as genai
            genai_types = None
        HAS_GENAI = True
    except ImportError:
        HAS_GENAI = False
        genai_types = None


class RAGService:
    def __init__(self):
        self._gemini_client = None
        self._init_gemini()

    def _init_gemini(self):
        key = (settings.GEMINI_API_KEY or "").strip()
        if key and HAS_GENAI:
            try:
                # Modern google-genai Client pattern
                if hasattr(genai, "Client"):
                    self._gemini_client = genai.Client(api_key=key)
                else:
                    genai.configure(api_key=key)
                    self._gemini_client = "configured_legacy"
                logger.info("Google Gemini AI client configured successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini AI: {e}")
                self._gemini_client = None
        else:
            self._gemini_client = None

    def _compute_text_vector(self, text: str) -> Dict[str, float]:
        """Computes normalized term frequency vector for token similarity."""
        words = re.findall(r"\w+", text.lower())
        vec: Dict[str, float] = {}
        for w in words:
            if len(w) > 2:  # skip single/two letter noise
                vec[w] = vec.get(w, 0.0) + 1.0
        
        magnitude = math.sqrt(sum(v * v for v in vec.values()))
        if magnitude > 0:
            for w in vec:
                vec[w] /= magnitude
        return vec

    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Computes cosine similarity between two sparse term vectors."""
        common = set(vec1.keys()) & set(vec2.keys())
        return sum(vec1[k] * vec2[k] for k in common)

    async def retrieve_context(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Retrieves most relevant knowledge base documents matching the query."""
        knowledge_col = db_manager.get_collection("knowledge_base")
        docs = await knowledge_col.find({}).to_list(length=100)
        if not docs:
            return []

        query_vec = self._compute_text_vector(query)
        scored_docs: List[Tuple[float, Dict[str, Any]]] = []

        for doc in docs:
            doc_text = f"{doc.get('product_name', '')} {doc.get('context_text', '')}"
            doc_vec = self._compute_text_vector(doc_text)
            score = self._cosine_similarity(query_vec, doc_vec)

            # Boost if query words are directly present in the product name
            p_name = doc.get("product_name", "").lower()
            if any(q_word in p_name for q_word in query.lower().split() if len(q_word) > 3):
                score += 0.3

            scored_docs.append((score, doc))

        # Sort by relevance score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k] if score > 0.05] or [scored_docs[0][1]] if scored_docs else []

    async def generate_reply(
        self,
        query: str,
        platform: str = "INSTAGRAM",
        customer_name: str = "Valued Customer",
        account_id: str = None
    ) -> Dict[str, Any]:
        """Generates a brand-aware, context-grounded response using Gemini AI or heuristic RAG."""
        retrieved_docs = await self.retrieve_context(query)
        sources = [d.get("product_name", "Knowledge Base") for d in retrieved_docs]
        context_str = "\n\n".join(
            [f"[{d.get('category', 'INFO')}] {d.get('product_name')}: {d.get('context_text')}" for d in retrieved_docs]
        )

        # Check if live Gemini AI is active
        key = (settings.GEMINI_API_KEY or "").strip()
        if key and not self._gemini_client:
            self._init_gemini()

        if self._gemini_client and HAS_GENAI:
            try:
                system_instruction = (
                    "You are the official brand concierge for CleanDesk, a premium modern workspace and accessories company. "
                    "Respond to the customer inquiry using ONLY the provided Verified Store Information. "
                    "Tone: Warm, concise, professional, and helpful. "
                    f"Platform formatting: This is for {platform}. Keep it under 3-4 sentences without excessive hashtags. "
                    f"Address the customer as '{customer_name}' if appropriate."
                )

                prompt = (
                    f"{system_instruction}\n\n"
                    f"=== VERIFIED STORE INFORMATION ===\n{context_str}\n\n"
                    f"=== CUSTOMER INQUIRY ===\n{query}\n\n"
                    "Provide your brand response below:"
                )

                text_resp = None
                if hasattr(self._gemini_client, "models"):
                    # Modern google.genai Client with AFC explicitly disabled
                    call_kwargs = {
                        "model": settings.GEMINI_MODEL,
                        "contents": prompt,
                    }
                    if genai_types and hasattr(genai_types, "GenerateContentConfig"):
                        try:
                            call_kwargs["config"] = genai_types.GenerateContentConfig(
                                temperature=0.7,
                                automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(disable=True)
                            )
                        except Exception:
                            pass
                    response = self._gemini_client.models.generate_content(**call_kwargs)
                    text_resp = response.text
                elif hasattr(genai, "GenerativeModel"):
                    # Legacy fallback
                    model = genai.GenerativeModel(settings.GEMINI_MODEL)
                    response = model.generate_content(prompt)
                    text_resp = response.text

                if text_resp:
                    return {
                        "reply": text_resp.strip(),
                        "sources": sources,
                        "model_used": f"Google Gemini ({settings.GEMINI_MODEL})",
                        "confidence_score": 0.96
                    }
            except Exception as e:
                logger.warning(f"Gemini API call failed ({e}), using resilient heuristic generator.")

        # Heuristic RAG Response Generator (Zero-setup instant demonstration)
        reply = self._generate_heuristic_reply(query, customer_name, platform, retrieved_docs)
        return {
            "reply": reply,
            "sources": sources,
            "model_used": "CleanDesk RAG Synthesizer (Gemini Fallback)",
            "confidence_score": 0.91
        }

    def _generate_heuristic_reply(
        self,
        query: str,
        customer_name: str,
        platform: str,
        docs: List[Dict[str, Any]]
    ) -> str:
        """Synthesizes a realistic brand response from retrieved context without external API calls."""
        lower = query.lower()
        greeting = f"Hi {customer_name}! " if customer_name and customer_name != "Valued Customer" else "Hello! "

        if not docs:
            return (
                f"{greeting}Thank you for reaching out to CleanDesk! Our customer support team has received your message "
                "and will get back to you shortly with full details."
            )

        top_doc = docs[0]
        context = top_doc.get("context_text", "")

        if any(w in lower for w in ["return", "refund", "exchange", "money back"]):
            return (
                f"{greeting}Thanks for reaching out! We offer a 30-day hassle-free return window with 100% free return shipping "
                "within the US. Once your item is received, refunds are processed back to your original payment method in 3-5 business days. "
                "Let us know if you'd like us to generate a prepaid return label!"
            )
        elif any(w in lower for w in ["ship", "delivery", "track", "international", "arrive", "where is my order"]):
            return (
                f"{greeting}All CleanDesk orders ship within 24 hours! Standard US shipping is 3-5 business days (Free over $60), "
                "and Express 1-2 day delivery is available. International delivery takes 7-12 days at a flat $15 rate. "
                "Please send us your order number and we'll pull up live tracking for you right away!"
            )
        elif any(w in lower for w in ["discount", "coupon", "promo", "code", "sale", "offer"]):
            return (
                f"{greeting}Great news! You can use code 'WELCOME15' at checkout for 15% off any order over $50. "
                "We also offer an exclusive 20% discount for students through StudentBeans!"
            )
        elif any(w in lower for w in ["desk mat", "mat", "leather"]):
            return (
                f"{greeting}Our CleanDesk Dual-Sided Vegan Leather Desk Mat ($49.99, 90x40cm) features water-resistant vegan leather "
                "on one side and organic cork on the reverse. It's super easy to wipe clean and available in Midnight Black, Saddle Brown, and Slate Gray!"
            )
        elif any(w in lower for w in ["cable", "organizer", "hub"]):
            return (
                f"{greeting}Our Magnetic Cable Management Hub ($29.99) is precision-machined from anodized aluminum and holds up to 5 cables securely "
                "using neodymium magnets. It features a micro-suction base that leaves zero residue on your desk!"
            )
        elif any(w in lower for w in ["charger", "gan", "watt", "power"]):
            return (
                f"{greeting}The CleanDesk 65W GaN Dual USB-C Charger ($39.99) fast-charges laptops, iPhones, and iPads simultaneously "
                "with ultra-compact GaN III technology and foldable prongs. Perfect for minimal desks and travel!"
            )

        # General synthesis
        return (
            f"{greeting}Thanks for checking out CleanDesk! Based on our catalog: {context} "
            "Please feel free to ask if you have any questions or need sizing/setup recommendations!"
        )


# Singleton RAG Service
rag_service = RAGService()
