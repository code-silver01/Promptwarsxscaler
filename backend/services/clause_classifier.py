"""
Layer 2 — Clause Classification Service.

Classifies clauses using Gemini zero-shot classification,
detects vague qualifiers, and identifies contradictions.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from backend.models.schemas import Clause, ClauseCategory
from backend.utils.gemini_client import call_gemini

logger = logging.getLogger("lexguard.clause_classifier")

VAGUE_QUALIFIERS: list[str] = [
    "reasonable", "at our discretion", "may", "without notice",
    "as appropriate", "at any time", "sole judgment", "in our opinion",
    "from time to time", "as deemed necessary",
]

_CLASSIFICATION_SYSTEM_PROMPT: str = (
    "You are a legal clause classifier. Classify the clause into exactly one of: "
    "IP_TRANSFER, NON_COMPETE, ARBITRATION, AUTO_RENEWAL, LIABILITY_LIMITATION, "
    "DATA_COLLECTION, TERMINATION, PAYMENT_PENALTY, INDEMNIFICATION, JURISDICTION, AMBIGUOUS. "
    'Return ONLY JSON: {"category": "NAME", "confidence": 0.0, "reasoning": "brief"}'
)

_CONTRADICTION_SYSTEM_PROMPT: str = (
    "You are a legal analyst detecting contradictions between two contract clauses. "
    'Return ONLY JSON: {"is_contradiction": true/false, "explanation": "brief"}'
)


def detect_vague_qualifiers(clause_text: str) -> list[str]:
    """Detect vague qualifier phrases in a clause text.

    Args:
        clause_text: The text to analyze.

    Returns:
        List of detected vague qualifier phrases.
    """
    text_lower = clause_text.lower()
    return [q for q in VAGUE_QUALIFIERS if q in text_lower]


async def classify_single_clause(clause: Clause) -> Clause:
    """Classify a single clause using Gemini.

    Args:
        clause: The clause to classify.

    Returns:
        Updated clause with category set.
    """
    try:
        result = await call_gemini(
            prompt=clause.text,
            system_prompt=_CLASSIFICATION_SYSTEM_PROMPT,
            model_name="gemini-1.5-flash",
            use_cache=True, temperature=0.2,
        )
        category_str = result.get("category", "AMBIGUOUS")
        try:
            clause.category = ClauseCategory(category_str)
        except ValueError:
            clause.category = ClauseCategory.AMBIGUOUS
    except Exception as exc:
        clause.category = ClauseCategory.AMBIGUOUS
        logger.error(json.dumps({
            "service": "clause_classifier", "clause_id": clause.id,
            "status": "error", "error": str(exc),
        }))
    return clause


async def classify_clauses(clauses: list[Clause]) -> list[Clause]:
    """Classify all clauses in parallel.

    Args:
        clauses: List of clauses to classify.

    Returns:
        List of clauses with categories assigned.
    """
    tasks = [classify_single_clause(c) for c in clauses]
    return list(await asyncio.gather(*tasks))


async def detect_contradictions(clauses: list[Clause]) -> list[dict]:
    """Detect contradictions between clause pairs.

    Args:
        clauses: List of classified clauses.

    Returns:
        List of contradiction dictionaries.
    """
    contradictions: list[dict] = []
    pairs = _identify_conflict_pairs(clauses)
    for ca, cb in pairs:
        try:
            prompt = f"Clause A: {ca.text}\n\nClause B: {cb.text}"
            result = await call_gemini(
                prompt=prompt, system_prompt=_CONTRADICTION_SYSTEM_PROMPT,
                model_name="gemini-1.5-flash", use_cache=True, temperature=0.2,
            )
            if result.get("is_contradiction"):
                contradictions.append({
                    "clause_a_id": ca.id, "clause_b_id": cb.id,
                    "explanation": result.get("explanation", ""),
                })
        except Exception as exc:
            logger.warning(json.dumps({
                "service": "clause_classifier", "status": "error", "error": str(exc),
            }))
    return contradictions


def _identify_conflict_pairs(clauses: list[Clause]) -> list[tuple[Clause, Clause]]:
    """Identify clause pairs that may conflict by category.

    Args:
        clauses: Classified clauses.

    Returns:
        List of (clause_a, clause_b) tuples.
    """
    conflicts = {
        ClauseCategory.TERMINATION: {ClauseCategory.AUTO_RENEWAL},
        ClauseCategory.LIABILITY_LIMITATION: {ClauseCategory.INDEMNIFICATION},
        ClauseCategory.IP_TRANSFER: {ClauseCategory.NON_COMPETE},
    }
    pairs = []
    for i, ca in enumerate(clauses):
        if ca.category is None:
            continue
        targets = conflicts.get(ca.category, set())
        for cb in clauses[i + 1:]:
            if cb.category in targets:
                pairs.append((ca, cb))
    return pairs
