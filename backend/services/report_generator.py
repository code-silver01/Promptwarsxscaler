"""
Layer 8 — Report Generation Service.

Assembles the final structured analysis report from all
processing layers into a complete, JSON-serializable output.
"""

from __future__ import annotations

import json
import logging
from collections import Counter

from backend.models.schemas import (
    AggregateScoreBreakdown, AnalysisReport, CategoryHeatmapEntry,
    ClauseReport, RiskTier,
)

logger = logging.getLogger("lexguard.report_generator")

# Document type detection keywords
_DOC_TYPE_KEYWORDS: dict[str, list[str]] = {
    "Employment Contract": ["employee", "employer", "employment", "salary", "benefits"],
    "Freelance Agreement": ["freelancer", "contractor", "independent contractor", "deliverables"],
    "Rental Agreement": ["tenant", "landlord", "lease", "rent", "premises"],
    "Subscription T&Cs": ["subscription", "recurring", "plan", "subscriber"],
    "Vendor Agreement": ["vendor", "supplier", "purchase order", "procurement"],
    "Privacy Policy": ["personal data", "privacy", "cookies", "data controller"],
    "Offer Letter": ["offer", "position", "start date", "compensation package"],
    "Non-Disclosure Agreement": ["confidential", "nda", "non-disclosure", "proprietary"],
}


def detect_document_type(clauses: list[ClauseReport]) -> str:
    """Detect the type of legal document from clause content.

    Args:
        clauses: List of clause reports.

    Returns:
        Detected document type string.
    """
    all_text = " ".join(
        cr.clause.text.lower() for cr in clauses
    )
    scores: dict[str, int] = {}
    for doc_type, keywords in _DOC_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in all_text)
        scores[doc_type] = score

    best_type = max(scores, key=scores.get)  # type: ignore
    if scores[best_type] == 0:
        return "Legal Agreement"
    return best_type


def build_category_heatmap(
    clause_reports: list[ClauseReport],
) -> list[CategoryHeatmapEntry]:
    """Build category heatmap from flagged clauses.

    Args:
        clause_reports: All clause reports.

    Returns:
        List of category counts sorted by frequency.
    """
    counter: Counter = Counter()
    for cr in clause_reports:
        if cr.category and cr.severity:
            counter[cr.category.value] += 1

    entries = [
        CategoryHeatmapEntry(category=cat, count=count)
        for cat, count in counter.most_common()
    ]
    return entries


def generate_report(
    clause_reports: list[ClauseReport],
    aggregate_score: float,
    score_breakdown: AggregateScoreBreakdown,
    risk_tier: RiskTier,
    contradictions: list[dict],
) -> AnalysisReport:
    """Assemble the final analysis report.

    Args:
        clause_reports: All per-clause analysis results.
        aggregate_score: Document-level risk score.
        score_breakdown: Traceable score derivation.
        risk_tier: Determined risk tier.
        contradictions: Detected clause contradictions.

    Returns:
        Complete AnalysisReport.
    """
    flagged = sum(1 for cr in clause_reports if cr.severity is not None)
    doc_type = detect_document_type(clause_reports)
    heatmap = build_category_heatmap(clause_reports)

    # Sort clause reports by severity (HIGH first)
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    sorted_reports = sorted(
        clause_reports,
        key=lambda cr: severity_order.get(
            cr.severity.value if cr.severity else "LOW", 3
        ),
    )

    report = AnalysisReport(
        document_type=doc_type,
        total_clauses=len(clause_reports),
        flagged_clauses=flagged,
        risk_tier=risk_tier,
        aggregate_risk_score=aggregate_score,
        score_breakdown=score_breakdown,
        clause_reports=sorted_reports,
        category_heatmap=heatmap,
        contradictions=contradictions,
    )

    logger.info(json.dumps({
        "service": "report_generator", "operation": "generate_report",
        "document_type": doc_type, "total_clauses": len(clause_reports),
        "flagged_clauses": flagged, "risk_tier": risk_tier.value,
        "aggregate_score": aggregate_score, "status": "success",
    }))

    return report
