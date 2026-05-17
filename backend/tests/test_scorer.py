"""
Tests for Layer 7 — Risk Scoring Engine.

Tests score range, severity impact, component summation,
and risk tier threshold accuracy.
"""

from __future__ import annotations

import pytest

from backend.models.schemas import ClauseCategory, RiskTier, Severity
from backend.services.risk_scorer import (
    calculate_aggregate_score, calculate_benchmark_deviation,
    determine_risk_tier, score_clause,
)


class TestClauseScoring:
    """Tests for per-clause risk scoring."""

    def test_score_within_0_100_range(self):
        """Aggregate score must be between 0 and 100."""
        breakdown = score_clause(
            Severity.HIGH, ClauseCategory.IP_TRANSFER, 80.0,
        )
        agg_score, _ = calculate_aggregate_score([breakdown])
        assert 0 <= agg_score <= 100

    def test_high_severity_clause_increases_score(self):
        """HIGH severity should produce higher score than LOW."""
        high_breakdown = score_clause(
            Severity.HIGH, ClauseCategory.IP_TRANSFER, 50.0,
        )
        low_breakdown = score_clause(
            Severity.LOW, ClauseCategory.IP_TRANSFER, 50.0,
        )
        assert high_breakdown.final_score > low_breakdown.final_score

    def test_score_components_sum_correctly(self):
        """Score should be product of severity × weight × deviation."""
        breakdown = score_clause(
            Severity.MEDIUM, ClauseCategory.NON_COMPETE, 60.0,
        )
        expected = (
            breakdown.base_severity_score
            * breakdown.category_weight
            * breakdown.benchmark_deviation
        )
        assert abs(breakdown.final_score - expected) < 0.01

    def test_ip_transfer_weighted_higher(self):
        """IP_TRANSFER has weight 1.5, should score higher than TERMINATION."""
        ip_score = score_clause(
            Severity.HIGH, ClauseCategory.IP_TRANSFER, 50.0,
        )
        term_score = score_clause(
            Severity.HIGH, ClauseCategory.TERMINATION, 50.0,
        )
        assert ip_score.final_score > term_score.final_score


class TestBenchmarkDeviation:
    """Tests for benchmark deviation calculation."""

    def test_zero_percentile(self):
        """0 percentile should give 0.5 multiplier."""
        assert calculate_benchmark_deviation(0.0) == 0.5

    def test_full_percentile(self):
        """100 percentile should give 1.5 multiplier."""
        assert calculate_benchmark_deviation(100.0) == 1.5

    def test_mid_percentile(self):
        """50 percentile should give 1.0 multiplier."""
        assert calculate_benchmark_deviation(50.0) == 1.0


class TestRiskTiers:
    """Tests for risk tier determination."""

    def test_risk_tier_thresholds(self):
        """Verify all tier boundaries."""
        assert determine_risk_tier(0) == RiskTier.LOW
        assert determine_risk_tier(25) == RiskTier.LOW
        assert determine_risk_tier(26) == RiskTier.MODERATE
        assert determine_risk_tier(50) == RiskTier.MODERATE
        assert determine_risk_tier(51) == RiskTier.HIGH
        assert determine_risk_tier(75) == RiskTier.HIGH
        assert determine_risk_tier(76) == RiskTier.CRITICAL
        assert determine_risk_tier(100) == RiskTier.CRITICAL

    def test_empty_clauses_give_zero(self):
        """No clauses should give 0 score."""
        score, breakdown = calculate_aggregate_score([])
        assert score == 0.0
        assert breakdown.clause_count == 0
