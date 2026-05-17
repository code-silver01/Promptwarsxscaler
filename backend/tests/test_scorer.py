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

    def test_score_clamped_at_100(self):
        """Aggregate score should never exceed 100."""
        # Create many HIGH severity, max weight, max deviation clauses
        breakdowns = [
            score_clause(Severity.HIGH, ClauseCategory.IP_TRANSFER, 100.0)
            for _ in range(100)
        ]
        score, _ = calculate_aggregate_score(breakdowns)
        assert score <= 100.0

    def test_score_clamped_at_zero(self):
        """Aggregate score should never be negative."""
        breakdown = score_clause(Severity.LOW, ClauseCategory.AMBIGUOUS, 0.0)
        score, _ = calculate_aggregate_score([breakdown])
        assert score >= 0.0

    def test_unknown_category_defaults_to_weight_one(self):
        """Unknown category should use default weight of 1.0."""
        # AMBIGUOUS has weight 1.0
        breakdown = score_clause(Severity.HIGH, ClauseCategory.AMBIGUOUS, 50.0)
        assert breakdown.category_weight == 1.0

    def test_aggregate_breakdown_clause_count_correct(self):
        """AggregateScoreBreakdown should report correct clause count."""
        breakdowns = [
            score_clause(Severity.HIGH, ClauseCategory.IP_TRANSFER, 50.0),
            score_clause(Severity.MEDIUM, ClauseCategory.NON_COMPETE, 50.0),
            score_clause(Severity.LOW, ClauseCategory.TERMINATION, 50.0),
        ]
        _, breakdown = calculate_aggregate_score(breakdowns)
        assert breakdown.clause_count == 3

    def test_risk_tier_boundary_exactly_25_is_low(self):
        """Score of exactly 25 should be LOW tier."""
        assert determine_risk_tier(25.0) == RiskTier.LOW

    def test_risk_tier_boundary_exactly_50_is_moderate(self):
        """Score of exactly 50 should be MODERATE tier."""
        assert determine_risk_tier(50.0) == RiskTier.MODERATE

    def test_risk_tier_boundary_exactly_75_is_high(self):
        """Score of exactly 75 should be HIGH tier."""
        assert determine_risk_tier(75.0) == RiskTier.HIGH

    def test_risk_tier_score_zero_is_low(self):
        """Score of 0 should be LOW tier."""
        assert determine_risk_tier(0.0) == RiskTier.LOW

    def test_risk_tier_score_100_is_critical(self):
        """Score of 100 should be CRITICAL tier."""
        assert determine_risk_tier(100.0) == RiskTier.CRITICAL
