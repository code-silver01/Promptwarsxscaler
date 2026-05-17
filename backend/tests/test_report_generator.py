"""
Tests for Layer 8 — Report Generator.

Tests document type detection, category heatmap construction,
severity-based sorting, and full report assembly.
"""

from __future__ import annotations

import pytest

from backend.models.schemas import (
    AggregateScoreBreakdown,
    AnalysisReport,
    CategoryHeatmapEntry,
    Clause,
    ClauseCategory,
    ClauseReport,
    ClauseScoreBreakdown,
    RiskTier,
    Severity,
)
from backend.services.report_generator import (
    build_category_heatmap,
    detect_document_type,
    generate_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_clause(idx: int, text: str, section: str = "General") -> Clause:
    """Create a minimal Clause for testing."""
    return Clause(id=f"clause_{idx:03d}", text=text, section=section)


def _make_clause_report(
    idx: int,
    text: str,
    category: ClauseCategory | None = None,
    severity: Severity | None = None,
) -> ClauseReport:
    """Create a ClauseReport with optional category and severity."""
    clause = _make_clause(idx, text)
    return ClauseReport(clause=clause, category=category, severity=severity)


def _make_score_breakdown() -> AggregateScoreBreakdown:
    """Create a minimal AggregateScoreBreakdown."""
    return AggregateScoreBreakdown(
        total_clause_score=10.0,
        max_possible_score=100.0,
        raw_percentage=10.0,
        clause_count=2,
    )


# ---------------------------------------------------------------------------
# detect_document_type
# ---------------------------------------------------------------------------

class TestDetectDocumentType:
    """Tests for document type detection from clause content."""

    def test_employment_contract_detected(self):
        """Clauses with employment keywords should detect Employment Contract."""
        reports = [
            _make_clause_report(1, "The Employee agrees to perform duties for the Employer."),
            _make_clause_report(2, "Salary and benefits will be reviewed annually."),
        ]
        doc_type = detect_document_type(reports)
        assert doc_type == "Employment Contract"

    def test_nda_detected(self):
        """Clauses with NDA keywords should detect Non-Disclosure Agreement."""
        reports = [
            _make_clause_report(1, "All confidential information and proprietary data is protected."),
            _make_clause_report(2, "This non-disclosure agreement covers all nda obligations."),
        ]
        doc_type = detect_document_type(reports)
        assert doc_type == "Non-Disclosure Agreement"

    def test_rental_agreement_detected(self):
        """Clauses with rental keywords should detect Rental Agreement."""
        reports = [
            _make_clause_report(1, "The tenant agrees to pay rent monthly to the landlord."),
            _make_clause_report(2, "The lease covers the premises at the agreed address."),
        ]
        doc_type = detect_document_type(reports)
        assert doc_type == "Rental Agreement"

    def test_privacy_policy_detected(self):
        """Clauses with privacy keywords should detect Privacy Policy."""
        reports = [
            _make_clause_report(1, "We collect personal data and use cookies on our platform."),
            _make_clause_report(2, "The data controller is responsible for privacy compliance."),
        ]
        doc_type = detect_document_type(reports)
        assert doc_type == "Privacy Policy"

    def test_unknown_document_falls_back_to_legal_agreement(self):
        """Clauses with no matching keywords should fall back to Legal Agreement."""
        reports = [
            _make_clause_report(1, "The parties agree to the terms herein."),
            _make_clause_report(2, "This document is binding upon execution."),
        ]
        doc_type = detect_document_type(reports)
        assert doc_type == "Legal Agreement"

    def test_offer_letter_detected(self):
        """Clauses with offer letter keywords should detect Offer Letter."""
        reports = [
            _make_clause_report(1, "This offer outlines your position and start date."),
            _make_clause_report(2, "Your compensation package includes base salary and equity."),
        ]
        doc_type = detect_document_type(reports)
        assert doc_type == "Offer Letter"

    def test_empty_clauses_returns_legal_agreement(self):
        """Empty clause list should return Legal Agreement."""
        doc_type = detect_document_type([])
        assert doc_type == "Legal Agreement"


# ---------------------------------------------------------------------------
# build_category_heatmap
# ---------------------------------------------------------------------------

class TestBuildCategoryHeatmap:
    """Tests for category heatmap construction."""

    def test_heatmap_counts_categories(self):
        """Heatmap should count flagged clauses per category."""
        reports = [
            _make_clause_report(1, "text", ClauseCategory.IP_TRANSFER, Severity.HIGH),
            _make_clause_report(2, "text", ClauseCategory.IP_TRANSFER, Severity.MEDIUM),
            _make_clause_report(3, "text", ClauseCategory.NON_COMPETE, Severity.HIGH),
        ]
        heatmap = build_category_heatmap(reports)
        counts = {e.category: e.count for e in heatmap}
        assert counts["IP_TRANSFER"] == 2
        assert counts["NON_COMPETE"] == 1

    def test_heatmap_sorted_by_frequency(self):
        """Heatmap entries should be sorted by count descending."""
        reports = [
            _make_clause_report(1, "text", ClauseCategory.NON_COMPETE, Severity.HIGH),
            _make_clause_report(2, "text", ClauseCategory.IP_TRANSFER, Severity.HIGH),
            _make_clause_report(3, "text", ClauseCategory.IP_TRANSFER, Severity.MEDIUM),
            _make_clause_report(4, "text", ClauseCategory.IP_TRANSFER, Severity.LOW),
        ]
        heatmap = build_category_heatmap(reports)
        assert heatmap[0].category == "IP_TRANSFER"
        assert heatmap[0].count == 3

    def test_heatmap_excludes_unflagged_clauses(self):
        """Clauses without severity should not appear in heatmap."""
        reports = [
            _make_clause_report(1, "text", ClauseCategory.IP_TRANSFER, None),
            _make_clause_report(2, "text", None, Severity.HIGH),
        ]
        heatmap = build_category_heatmap(reports)
        assert len(heatmap) == 0

    def test_empty_reports_returns_empty_heatmap(self):
        """Empty clause list should return empty heatmap."""
        heatmap = build_category_heatmap([])
        assert heatmap == []

    def test_heatmap_returns_list_of_entries(self):
        """Heatmap should return a list of CategoryHeatmapEntry objects."""
        reports = [
            _make_clause_report(1, "text", ClauseCategory.ARBITRATION, Severity.HIGH),
        ]
        heatmap = build_category_heatmap(reports)
        assert isinstance(heatmap, list)
        assert isinstance(heatmap[0], CategoryHeatmapEntry)


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------

class TestGenerateReport:
    """Tests for full report assembly."""

    def _make_full_reports(self) -> list[ClauseReport]:
        """Create a set of clause reports with mixed severities."""
        return [
            _make_clause_report(
                1,
                "The Employee agrees to perform duties for the Employer.",
                ClauseCategory.IP_TRANSFER,
                Severity.HIGH,
            ),
            _make_clause_report(
                2,
                "Salary and benefits will be reviewed annually by the employer.",
                ClauseCategory.NON_COMPETE,
                Severity.MEDIUM,
            ),
            _make_clause_report(
                3,
                "The employee may terminate employment with two weeks notice.",
                ClauseCategory.TERMINATION,
                Severity.LOW,
            ),
        ]

    def test_report_has_correct_total_clauses(self):
        """Report total_clauses should match input count."""
        reports = self._make_full_reports()
        score_breakdown = _make_score_breakdown()
        report = generate_report(reports, 45.0, score_breakdown, RiskTier.MODERATE, [])
        assert report.total_clauses == 3

    def test_report_counts_flagged_clauses(self):
        """Report flagged_clauses should count clauses with severity."""
        reports = self._make_full_reports()
        score_breakdown = _make_score_breakdown()
        report = generate_report(reports, 45.0, score_breakdown, RiskTier.MODERATE, [])
        assert report.flagged_clauses == 3

    def test_report_risk_tier_matches_input(self):
        """Report risk_tier should match the provided tier."""
        reports = self._make_full_reports()
        score_breakdown = _make_score_breakdown()
        report = generate_report(reports, 80.0, score_breakdown, RiskTier.CRITICAL, [])
        assert report.risk_tier == RiskTier.CRITICAL

    def test_report_aggregate_score_matches_input(self):
        """Report aggregate_risk_score should match the provided score."""
        reports = self._make_full_reports()
        score_breakdown = _make_score_breakdown()
        report = generate_report(reports, 55.5, score_breakdown, RiskTier.HIGH, [])
        assert report.aggregate_risk_score == 55.5

    def test_report_clauses_sorted_high_first(self):
        """Clause reports should be sorted HIGH → MEDIUM → LOW."""
        reports = self._make_full_reports()
        score_breakdown = _make_score_breakdown()
        report = generate_report(reports, 45.0, score_breakdown, RiskTier.MODERATE, [])
        severities = [
            cr.severity.value for cr in report.clause_reports if cr.severity
        ]
        assert severities == ["HIGH", "MEDIUM", "LOW"]

    def test_report_includes_contradictions(self):
        """Report should include provided contradictions."""
        reports = self._make_full_reports()
        score_breakdown = _make_score_breakdown()
        contradictions = [{"clause_a_id": "clause_001", "clause_b_id": "clause_002", "explanation": "conflict"}]
        report = generate_report(reports, 45.0, score_breakdown, RiskTier.MODERATE, contradictions)
        assert len(report.contradictions) == 1
        assert report.contradictions[0]["clause_a_id"] == "clause_001"

    def test_report_returns_analysis_report_instance(self):
        """generate_report should return an AnalysisReport instance."""
        reports = self._make_full_reports()
        score_breakdown = _make_score_breakdown()
        report = generate_report(reports, 45.0, score_breakdown, RiskTier.MODERATE, [])
        assert isinstance(report, AnalysisReport)

    def test_report_with_empty_clauses(self):
        """Report with no clauses should have zero flagged and empty heatmap."""
        score_breakdown = AggregateScoreBreakdown(
            total_clause_score=0.0,
            max_possible_score=1.0,
            raw_percentage=0.0,
            clause_count=0,
        )
        report = generate_report([], 0.0, score_breakdown, RiskTier.LOW, [])
        assert report.total_clauses == 0
        assert report.flagged_clauses == 0
        assert report.category_heatmap == []

    def test_report_category_heatmap_populated(self):
        """Report should include a populated category heatmap."""
        reports = self._make_full_reports()
        score_breakdown = _make_score_breakdown()
        report = generate_report(reports, 45.0, score_breakdown, RiskTier.MODERATE, [])
        assert len(report.category_heatmap) > 0
