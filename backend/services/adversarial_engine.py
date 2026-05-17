"""
Layer 3 — Adversarial Reasoning Engine.

Runs a three-agent debate (Risk, Defense, Verdict) on each
flagged clause using the Gemini API for adversarial analysis.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time

from backend.models.schemas import (
    Clause, ClauseCategory, DefenseAgentOutput,
    RiskAgentOutput, Severity, VerdictAgentOutput,
)
from backend.utils.gemini_client import call_gemini

logger = logging.getLogger("lexguard.adversarial_engine")

# Categories that trigger adversarial analysis
ADVERSARIAL_CATEGORIES: set[ClauseCategory] = {
    ClauseCategory.IP_TRANSFER, ClauseCategory.NON_COMPETE,
    ClauseCategory.ARBITRATION, ClauseCategory.LIABILITY_LIMITATION,
    ClauseCategory.DATA_COLLECTION, ClauseCategory.AUTO_RENEWAL,
    ClauseCategory.PAYMENT_PENALTY, ClauseCategory.INDEMNIFICATION,
    ClauseCategory.TERMINATION, ClauseCategory.JURISDICTION,
}

_RISK_AGENT_PROMPT: str = (
    "You are a strict legal adversary. Interpret the following contract clause "
    "in the worst possible way for the person signing it. Identify every way "
    "this clause could be exploited against them. Be specific. Reference exact phrases. "
    'Return JSON: {"risk_position": "...", "key_phrases": [...], "worst_case": "...", '
    '"reasoning": "step-by-step explanation of your analysis"}. '
    "Return only JSON."
)

_DEFENSE_AGENT_PROMPT: str = (
    "You are a legal defense counsel. Interpret the following contract clause "
    "in the most favorable way for the person signing it. Find every reasonable "
    "interpretation that protects their interests. Reference exact phrases. "
    'Return JSON: {"defense_position": "...", "favorable_phrases": [...], "best_case": "...", '
    '"reasoning": "step-by-step explanation of your analysis"}. '
    "Return only JSON."
)

_VERDICT_AGENT_PROMPT: str = (
    "You are a neutral legal analyst. You received two opposing interpretations "
    "of a contract clause. Synthesize them into a final verdict. Assign a severity "
    "(HIGH/MEDIUM/LOW), a confidence score (0.0-1.0), and explain in plain English "
    "in 2-3 sentences. Return only JSON: "
    '{"verdict": "...", "severity": "HIGH|MEDIUM|LOW", "confidence": 0.0, '
    '"risk_category": "...", "plain_english": "...", '
    '"reasoning": "step-by-step explanation of how you weighed both perspectives"}'
)


def should_analyze(clause: Clause) -> bool:
    """Check if a clause should undergo adversarial analysis.

    Args:
        clause: Classified clause.

    Returns:
        True if clause qualifies for adversarial analysis.
    """
    if clause.category is None:
        return False
    return clause.category in ADVERSARIAL_CATEGORIES


async def run_risk_agent(clause_text: str) -> RiskAgentOutput:
    """Run the Risk Agent (Red Team) on a clause.

    Args:
        clause_text: The clause text to analyze.

    Returns:
        Parsed Risk Agent output.

    Raises:
        RuntimeError: If the agent fails after retries.
    """
    result = await call_gemini(
        prompt=clause_text, system_prompt=_RISK_AGENT_PROMPT,
        model_name="gemini-1.5-pro", temperature=0.4,
    )
    return RiskAgentOutput(
        risk_position=result.get("risk_position", ""),
        key_phrases=result.get("key_phrases", []),
        worst_case=result.get("worst_case", ""),
        reasoning=result.get("reasoning", ""),
    )


async def run_defense_agent(clause_text: str) -> DefenseAgentOutput:
    """Run the Defense Agent (Blue Team) on a clause.

    Args:
        clause_text: The clause text to analyze.

    Returns:
        Parsed Defense Agent output.

    Raises:
        RuntimeError: If the agent fails after retries.
    """
    result = await call_gemini(
        prompt=clause_text, system_prompt=_DEFENSE_AGENT_PROMPT,
        model_name="gemini-1.5-pro", temperature=0.4,
    )
    return DefenseAgentOutput(
        defense_position=result.get("defense_position", ""),
        favorable_phrases=result.get("favorable_phrases", []),
        best_case=result.get("best_case", ""),
        reasoning=result.get("reasoning", ""),
    )


async def run_verdict_agent(
    clause_text: str,
    risk_output: RiskAgentOutput,
    defense_output: DefenseAgentOutput,
) -> VerdictAgentOutput:
    """Run the Verdict Agent to synthesize Risk and Defense positions.

    Args:
        clause_text: Original clause text.
        risk_output: Output from the Risk Agent.
        defense_output: Output from the Defense Agent.

    Returns:
        Parsed Verdict Agent output.
    """
    combined_prompt = (
        f"Original clause: {clause_text}\n\n"
        f"Risk Agent position: {risk_output.risk_position}\n"
        f"Key risk phrases: {', '.join(risk_output.key_phrases)}\n"
        f"Worst case: {risk_output.worst_case}\n\n"
        f"Defense Agent position: {defense_output.defense_position}\n"
        f"Favorable phrases: {', '.join(defense_output.favorable_phrases)}\n"
        f"Best case: {defense_output.best_case}"
    )
    result = await call_gemini(
        prompt=combined_prompt, system_prompt=_VERDICT_AGENT_PROMPT,
        model_name="gemini-1.5-pro", temperature=0.3,
    )
    severity_str = result.get("severity", "MEDIUM").upper()
    try:
        severity = Severity(severity_str)
    except ValueError:
        severity = Severity.MEDIUM

    confidence = max(0.0, min(1.0, float(result.get("confidence", 0.5))))

    # Generate a truly plain-English version via a separate fast call
    _PLAIN_ENGLISH_PROMPT = (
        "Explain this legal finding to a non-lawyer friend in 2-3 casual sentences. "
        "No legal jargon. No bullet points. Just talk like a friend warning another friend. "
        'Return ONLY a JSON object: {"plain_english": "..."}'
    )
    try:
        plain_result = await call_gemini(
            prompt=f"Legal finding: {result.get('verdict', '')}\nFor clause: {clause_text[:300]}",
            system_prompt=_PLAIN_ENGLISH_PROMPT,
            model_name="gemini-1.5-flash",
            temperature=0.5,
        )
        plain_english = plain_result.get("plain_english", result.get("plain_english", ""))
    except Exception:
        plain_english = result.get("plain_english", "")

    return VerdictAgentOutput(
        verdict=result.get("verdict", ""),
        severity=severity, confidence=confidence,
        risk_category=result.get("risk_category", ""),
        plain_english=plain_english,
        reasoning=result.get("reasoning", ""),
    )


async def analyze_clause(
    clause: Clause,
) -> tuple[RiskAgentOutput, DefenseAgentOutput, VerdictAgentOutput]:
    """Run full adversarial analysis on a single clause.

    Risk and Defense agents run in parallel; Verdict runs after both.

    Args:
        clause: The clause to analyze.

    Returns:
        Tuple of (risk_output, defense_output, verdict_output).
    """
    start = time.time()

    # Run Risk and Defense in parallel
    risk_output, defense_output = await asyncio.gather(
        run_risk_agent(clause.text),
        run_defense_agent(clause.text),
    )

    # Verdict requires both outputs — runs sequentially after
    verdict_output = await run_verdict_agent(
        clause.text, risk_output, defense_output,
    )

    duration_ms = (time.time() - start) * 1000
    logger.info(json.dumps({
        "service": "adversarial_engine",
        "operation": "analyze_clause",
        "clause_id": clause.id,
        "severity": verdict_output.severity.value,
        "confidence": verdict_output.confidence,
        "duration_ms": round(duration_ms, 2),
        "status": "success",
    }))

    return risk_output, defense_output, verdict_output
