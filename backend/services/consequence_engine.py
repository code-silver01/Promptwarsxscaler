"""
Layer 5 — Consequence Chain Simulation.

Generates real-world consequence chains for high-severity
clauses using structured Gemini prompts.
"""

from __future__ import annotations

import json
import logging

from backend.models.schemas import Clause, ConsequenceChain, VerdictAgentOutput
from backend.utils.gemini_client import call_gemini

logger = logging.getLogger("lexguard.consequence_engine")

_CONSEQUENCE_SYSTEM_PROMPT: str = (
    "Given this contract clause and the risk verdict, generate a real-world "
    "consequence chain for the person signing. Use plain, non-legal English. "
    "Be specific to the clause text. Return ONLY JSON: "
    '{"trigger_condition": "...", "immediate_consequence": "...", '
    '"downstream_impact": "...", "worst_case_scenario": "..."}'
)


async def generate_consequence_chain(
    clause: Clause,
    verdict: VerdictAgentOutput,
) -> ConsequenceChain:
    """Generate a consequence chain for a high-severity clause.

    Args:
        clause: The high-severity clause.
        verdict: Verdict agent output for context.

    Returns:
        Structured consequence chain.
    """
    prompt = (
        f"Contract clause: {clause.text}\n\n"
        f"Risk verdict: {verdict.verdict}\n"
        f"Severity: {verdict.severity.value}\n"
        f"Risk category: {verdict.risk_category}\n"
        f"Plain English: {verdict.plain_english}"
    )

    try:
        result = await call_gemini(
            prompt=prompt,
            system_prompt=_CONSEQUENCE_SYSTEM_PROMPT,
            model_name="gemini-1.5-pro",
            temperature=0.4,
        )

        chain = ConsequenceChain(
            trigger_condition=result.get("trigger_condition", ""),
            immediate_consequence=result.get("immediate_consequence", ""),
            downstream_impact=result.get("downstream_impact", ""),
            worst_case_scenario=result.get("worst_case_scenario", ""),
        )

        logger.info(json.dumps({
            "service": "consequence_engine",
            "clause_id": clause.id,
            "status": "success",
        }))
        return chain

    except Exception as exc:
        logger.error(json.dumps({
            "service": "consequence_engine",
            "clause_id": clause.id,
            "status": "error",
            "error": str(exc),
        }))
        return ConsequenceChain(
            trigger_condition="Analysis unavailable",
            immediate_consequence="Could not generate consequences",
            downstream_impact="Please review clause manually",
            worst_case_scenario="Unknown — manual review recommended",
        )
