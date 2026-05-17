"""
Layer 7 — Risk Scoring Engine.

Calculates traceable, auditable per-clause and aggregate
risk scores with full component breakdown.
"""

from __future__ import annotations

import json
import logging

from backend.models.schemas import (
    AggregateScoreBreakdown, ClauseCategory, ClauseScoreBreakdown,
    RiskTier, Severity,
)

logger = logging.getLogger("lexguard.risk_scorer")

# Severity numeric values
SEVERITY_SCORES: dict[Severity, float] = {
    Severity.HIGH: 3.0,
    Severity.MEDIUM: 2.0,
    Severity.LOW: 1.0,
}

# Category weight multipliers
CATEGORY_WEIGHTS: dict[ClauseCategory, float] = {
    ClauseCategory.IP_TRANSFER: 1.5,
    ClauseCategory.NON_COMPETE: 1.4,
    ClauseCategory.DATA_COLLECTION: 1.3,
    ClauseCategory.ARBITRATION: 1.3,
    ClauseCategory.AUTO_RENEWAL: 1.0,
    ClauseCategory.LIABILITY_LIMITATION: 1.0,
    ClauseCategory.TERMINATION: 1.0,
    ClauseCategory.PAYMENT_PENALTY: 1.0,
    ClauseCategory.INDEMNIFICATION: 1.0,
    ClauseCategory.JURISDICTION: 1.0,
    ClauseCategory.AMBIGUOUS: 1.0,
}


def calculate_benchmark_deviation(percentile: float) -> float:
    """Convert benchmark percentile to a deviation multiplier.

    Maps 0-100 percentile to 0.5-1.5 multiplier range.

    Args:
        percentile: Benchmark restrictiveness percentile (0-100).

    Returns:
        Deviation multiplier between 0.5 and 1.5.
    """
    return 0.5 + (percentile / 100.0)


def score_clause(
    severity: Severity,
    category: ClauseCategory,
    benchmark_percentile: float,
) -> ClauseScoreBreakdown:
    """Calculate the risk score for a single clause.

    Args:
        severity: Clause severity level.
        category: Clause category.
        benchmark_percentile: Benchmark deviation percentile.

    Returns:
        Traceable score breakdown.
    """
    base = SEVERITY_SCORES.get(severity, 1.0)
    weight = CATEGORY_WEIGHTS.get(category, 1.0)
    deviation = calculate_benchmark_deviation(benchmark_percentile)
    final = base * weight * deviation

    return ClauseScoreBreakdown(
        base_severity_score=base,
        category_weight=weight,
        benchmark_deviation=round(deviation, 3),
        final_score=round(final, 3),
    )


def calculate_aggregate_score(
    clause_scores: list[ClauseScoreBreakdown],
) -> tuple[float, AggregateScoreBreakdown]:
    """Calculate the aggregate document risk score.

    Args:
        clause_scores: List of per-clause score breakdowns.

    Returns:
        Tuple of (aggregate_score, breakdown).
    """
    if not clause_scores:
        breakdown = AggregateScoreBreakdown(
            total_clause_score=0.0, max_possible_score=1.0,
            raw_percentage=0.0, clause_count=0,
        )
        return 0.0, breakdown

    total = sum(cs.final_score for cs in clause_scores)
    # Max possible: each clause at HIGH severity, max weight, max deviation
    max_possible = len(clause_scores) * 3.0 * 1.5 * 1.5
    raw_pct = (total / max_possible) * 100 if max_possible > 0 else 0
    clamped = min(100.0, max(0.0, raw_pct))

    breakdown = AggregateScoreBreakdown(
        total_clause_score=round(total, 3),
        max_possible_score=round(max_possible, 3),
        raw_percentage=round(clamped, 2),
        clause_count=len(clause_scores),
    )

    logger.info(json.dumps({
        "service": "risk_scorer", "operation": "calculate_aggregate_score",
        "total": round(total, 3), "max_possible": round(max_possible, 3),
        "raw_percentage": round(clamped, 2), "status": "success",
    }))

    return round(clamped, 2), breakdown


def determine_risk_tier(score: float) -> RiskTier:
    """Determine the risk tier from aggregate score.

    Args:
        score: Aggregate risk score (0-100).

    Returns:
        Corresponding RiskTier.
    """
    if score <= 25:
        return RiskTier.LOW
    elif score <= 50:
        return RiskTier.MODERATE
    elif score <= 75:
        return RiskTier.HIGH
    else:
        return RiskTier.CRITICAL
