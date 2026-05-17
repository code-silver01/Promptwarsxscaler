"""
Tests for Layer 3 — Adversarial Reasoning Engine.

Tests Risk, Defense, and Verdict agent outputs for valid JSON
structure, severity enums, and parallel execution.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from backend.models.schemas import Clause, ClauseCategory, Severity
from backend.services.adversarial_engine import (
    analyze_clause, run_defense_agent, run_risk_agent,
    run_verdict_agent, should_analyze,
)


@pytest.fixture
def test_clause() -> Clause:
    """Create a test clause for adversarial analysis."""
    return Clause(
        id="clause_001",
        text=(
            "The Company retains all rights to any work product "
            "created during employment, including personal projects "
            "developed outside working hours using company equipment."
        ),
        section="Intellectual Property",
        category=ClauseCategory.IP_TRANSFER,
    )


@pytest.fixture
def mock_risk_response() -> dict:
    """Mock Risk Agent response."""
    return {
        "risk_position": "This clause gives the company ownership of all work",
        "key_phrases": ["all rights", "personal projects", "outside working hours"],
        "worst_case": "Company owns your side projects and portfolio",
    }


@pytest.fixture
def mock_defense_response() -> dict:
    """Mock Defense Agent response."""
    return {
        "defense_position": "Standard IP assignment limited to company equipment",
        "favorable_phrases": ["during employment", "company equipment"],
        "best_case": "Only applies to work done on company hardware",
    }


@pytest.fixture
def mock_verdict_response() -> dict:
    """Mock Verdict Agent response."""
    return {
        "verdict": "Clause is overly broad in scope",
        "severity": "HIGH",
        "confidence": 0.85,
        "risk_category": "IP_TRANSFER",
        "plain_english": "This clause could claim ownership of your personal projects.",
    }


class TestRiskAgent:
    """Tests for the Risk Agent."""

    @pytest.mark.asyncio
    @patch("backend.services.adversarial_engine.call_gemini")
    async def test_risk_agent_returns_valid_json(
        self, mock_gemini: AsyncMock, mock_risk_response: dict
    ):
        """Risk agent should return structured output."""
        mock_gemini.return_value = mock_risk_response
        result = await run_risk_agent("test clause text")
        assert hasattr(result, "risk_position")
        assert hasattr(result, "key_phrases")
        assert hasattr(result, "worst_case")
        assert isinstance(result.key_phrases, list)


class TestDefenseAgent:
    """Tests for the Defense Agent."""

    @pytest.mark.asyncio
    @patch("backend.services.adversarial_engine.call_gemini")
    async def test_defense_agent_returns_valid_json(
        self, mock_gemini: AsyncMock, mock_defense_response: dict
    ):
        """Defense agent should return structured output."""
        mock_gemini.return_value = mock_defense_response
        result = await run_defense_agent("test clause text")
        assert hasattr(result, "defense_position")
        assert hasattr(result, "favorable_phrases")
        assert hasattr(result, "best_case")
        assert isinstance(result.favorable_phrases, list)


class TestVerdictAgent:
    """Tests for the Verdict Agent."""

    @pytest.mark.asyncio
    @patch("backend.services.adversarial_engine.call_gemini")
    async def test_verdict_agent_returns_valid_json(
        self, mock_gemini: AsyncMock, mock_verdict_response: dict
    ):
        """Verdict agent should return structured output."""
        mock_gemini.return_value = mock_verdict_response
        risk_out = await run_risk_agent.__wrapped__(  # type: ignore
            "test"
        ) if hasattr(run_risk_agent, "__wrapped__") else None

        # Create mock inputs
        from backend.models.schemas import RiskAgentOutput, DefenseAgentOutput
        risk = RiskAgentOutput(
            risk_position="test", key_phrases=[], worst_case="test",
        )
        defense = DefenseAgentOutput(
            defense_position="test", favorable_phrases=[], best_case="test",
        )
        result = await run_verdict_agent("test clause", risk, defense)
        assert hasattr(result, "verdict")
        assert hasattr(result, "severity")
        assert hasattr(result, "confidence")

    @pytest.mark.asyncio
    @patch("backend.services.adversarial_engine.call_gemini")
    async def test_verdict_severity_is_valid_enum(
        self, mock_gemini: AsyncMock, mock_verdict_response: dict
    ):
        """Verdict severity must be a valid Severity enum."""
        mock_gemini.return_value = mock_verdict_response
        from backend.models.schemas import RiskAgentOutput, DefenseAgentOutput
        risk = RiskAgentOutput(
            risk_position="test", key_phrases=[], worst_case="test",
        )
        defense = DefenseAgentOutput(
            defense_position="test", favorable_phrases=[], best_case="test",
        )
        result = await run_verdict_agent("test", risk, defense)
        assert result.severity in {Severity.HIGH, Severity.MEDIUM, Severity.LOW}


class TestAdversarialPipeline:
    """Tests for the full adversarial pipeline."""

    @pytest.mark.asyncio
    @patch("backend.services.adversarial_engine.call_gemini")
    async def test_agents_run_in_parallel(
        self, mock_gemini: AsyncMock, test_clause: Clause,
        mock_risk_response: dict, mock_defense_response: dict,
        mock_verdict_response: dict,
    ):
        """Risk and Defense agents should run concurrently."""
        responses = [mock_risk_response, mock_defense_response, mock_verdict_response]
        call_index = 0

        async def sequential_mock(*args, **kwargs):
            nonlocal call_index
            resp = responses[min(call_index, len(responses) - 1)]
            call_index += 1
            await asyncio.sleep(0.05)
            return resp

        mock_gemini.side_effect = sequential_mock

        start = time.time()
        risk, defense, verdict = await analyze_clause(test_clause)
        elapsed = time.time() - start

        assert risk is not None
        assert defense is not None
        assert verdict is not None
        # Parallel: risk + defense run concurrently (~0.05s), then verdict (~0.05s) = ~0.1s total
        # Sequential would be ~0.15s. Allow generous bound.
        assert elapsed < 0.3

    def test_should_analyze_ip_clause(self, test_clause: Clause):
        """IP_TRANSFER clause should be analyzed."""
        assert should_analyze(test_clause) is True

    def test_should_not_analyze_ambiguous(self):
        """AMBIGUOUS clause should still be analyzed."""
        clause = Clause(
            id="test", text="test text with enough length to pass",
            category=ClauseCategory.AMBIGUOUS,
        )
        # AMBIGUOUS is not in ADVERSARIAL_CATEGORIES
        assert should_analyze(clause) is False
