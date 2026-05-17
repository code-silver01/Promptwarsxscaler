"""
Layer 6 — Negotiation Suggestion Generator.

Generates fairer clause alternatives using benchmark context
and Gemini-based rewriting for HIGH/MEDIUM severity clauses.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from backend.models.schemas import Clause, NegotiationSuggestion
from backend.utils.firestore_client import get_user_favorable_benchmark
from backend.utils.gemini_client import call_gemini

logger = logging.getLogger("lexguard.negotiation_engine")

_NEGOTIATION_SYSTEM_PROMPT: str = (
    "Rewrite the following risky contract clause in a fairer version that "
    "protects both parties. Use the provided benchmark as reference. "
    "Return ONLY JSON: "
    '{"suggested_text": "...", "why_safer": "..."}'
)


async def generate_suggestion(
    clause: Clause,
    category: str,
) -> Optional[NegotiationSuggestion]:
    """Generate a negotiation suggestion for a risky clause.

    Args:
        clause: The risky clause to suggest alternatives for.
        category: Clause category for benchmark lookup.

    Returns:
        NegotiationSuggestion or None if generation fails.
    """
    try:
        benchmark = await get_user_favorable_benchmark(category)
        benchmark_text = (
            benchmark.get("text", "No benchmark available")
            if benchmark else "No benchmark available"
        )

        prompt = (
            f"Risky clause: {clause.text}\n\n"
            f"User-favorable benchmark reference: {benchmark_text}"
        )

        result = await call_gemini(
            prompt=prompt,
            system_prompt=_NEGOTIATION_SYSTEM_PROMPT,
            model_name="gemini-2.5-pro",
            temperature=0.4,
        )

        suggestion = NegotiationSuggestion(
            original_clause_text=clause.text,
            suggested_alternative_text=result.get("suggested_text", ""),
            why_safer=result.get("why_safer", ""),
        )

        logger.info(json.dumps({
            "service": "negotiation_engine",
            "clause_id": clause.id,
            "status": "success",
        }))
        return suggestion

    except Exception as exc:
        logger.error(json.dumps({
            "service": "negotiation_engine",
            "clause_id": clause.id,
            "status": "error",
            "error": str(exc),
        }))
        return None
