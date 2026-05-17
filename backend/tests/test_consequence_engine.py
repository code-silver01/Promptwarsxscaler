"""
Tests for Layer 5 — Consequence Chain Engine.

Tests consequence chain generation, error fallback behavior,
and structured output validation with mocked Gemini calls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from backend.models.schemas import (
    Clause,
    ClauseCategory,
    ConsequenceChain,
    Severity,
    VerdictAgentOutput,
)
from backend.services.consequence_engine import generate_consequence_chain


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_clause(text: str = "The Company retains all IP rights.") -> Clause:
    """Create a minimal Clause for testing."""
    return Clause(
        id="clause_001",
        text=text,
        section="Intellectual Property",
        category=ClauseCategory.IP_TRANSFER,
    )


def _make_verdict(severity: Severity = Severity.HIGH) -> VerdictAgentOutput:
    """Create a minimal VerdictAgentOutput for testing."""
    return VerdictAgentOutput(
        verdict="This clause is overly broad and risky.",
        severity=severity,
        confidence=0.9,
        risk_category="IP_TRANSFER",
        plain_english="The company could claim ownership of your personal projects.",
    )


# ---------------------------------------------------------------------------
# generate_consequence_chain
# ---------------------------------------------------------------------------

class TestGenerateConsequenceChain:
    """Tests for consequence chain generation."""

    @pytest.mark.asyncio
    @patch("backend.services.consequence_engine.call_gemini")
    async def test_returns_consequence_chain_instance(
        self, mock_gemini: AsyncMock
    ):
        """Should return a ConsequenceChain instance on success."""
        mock_gemini.return_value = {
            "trigger_condition": "If you leave the company",
            "immediate_consequence": "Company claims your side projects",
            "downstream_impact": "You lose IP rights to personal work",
            "worst_case_scenario": "Lawsuit over personal project ownership",
        }
        clause = _make_clause()
        verdict = _make_verdict()
        result = await generate_consequence_chain(clause, verdict)
        assert isinstance(result, ConsequenceChain)

    @pytest.mark.asyncio
    @patch("backend.services.consequence_engine.call_gemini")
    async def test_consequence_chain_fields_populated(
        self, mock_gemini: AsyncMock
    ):
        """All four consequence chain fields should be populated."""
        mock_gemini.return_value = {
            "trigger_condition": "Upon termination",
            "immediate_consequence": "IP assignment takes effect",
            "downstream_impact": "Loss of future royalties",
            "worst_case_scenario": "Permanent loss of invention rights",
        }
        clause = _make_clause()
        verdict = _make_verdict()
        result = await generate_consequence_chain(clause, verdict)
        assert result.trigger_condition == "Upon termination"
        assert result.immediate_consequence == "IP assignment takes effect"
        assert result.downstream_impact == "Loss of future royalties"
        assert result.worst_case_scenario == "Permanent loss of invention rights"

    @pytest.mark.asyncio
    @patch("backend.services.consequence_engine.call_gemini")
    async def test_returns_fallback_on_gemini_failure(
        self, mock_gemini: AsyncMock
    ):
        """Should return a fallback ConsequenceChain when Gemini fails."""
        mock_gemini.side_effect = RuntimeError("Gemini API unavailable")
        clause = _make_clause()
        verdict = _make_verdict()
        result = await generate_consequence_chain(clause, verdict)
        assert isinstance(result, ConsequenceChain)
        # Fallback values should indicate unavailability
        assert "unavailable" in result.trigger_condition.lower() or \
               "could not" in result.immediate_consequence.lower() or \
               "manual" in result.downstream_impact.lower()

    @pytest.mark.asyncio
    @patch("backend.services.consequence_engine.call_gemini")
    async def test_fallback_chain_has_all_fields(
        self, mock_gemini: AsyncMock
    ):
        """Fallback ConsequenceChain should have all required fields non-empty."""
        mock_gemini.side_effect = Exception("Network error")
        clause = _make_clause()
        verdict = _make_verdict()
        result = await generate_consequence_chain(clause, verdict)
        assert result.trigger_condition
        assert result.immediate_consequence
        assert result.downstream_impact
        assert result.worst_case_scenario

    @pytest.mark.asyncio
    @patch("backend.services.consequence_engine.call_gemini")
    async def test_gemini_called_with_clause_text(
        self, mock_gemini: AsyncMock
    ):
        """Gemini should be called with the clause text in the prompt."""
        mock_gemini.return_value = {
            "trigger_condition": "test",
            "immediate_consequence": "test",
            "downstream_impact": "test",
            "worst_case_scenario": "test",
        }
        clause = _make_clause("Unique clause text for testing purposes.")
        verdict = _make_verdict()
        await generate_consequence_chain(clause, verdict)
        call_args = mock_gemini.call_args
        assert "Unique clause text for testing purposes." in call_args.kwargs.get(
            "prompt", call_args.args[0] if call_args.args else ""
        )

    @pytest.mark.asyncio
    @patch("backend.services.consequence_engine.call_gemini")
    async def test_partial_gemini_response_handled(
        self, mock_gemini: AsyncMock
    ):
        """Partial Gemini response (missing keys) should not raise."""
        mock_gemini.return_value = {
            "trigger_condition": "Some trigger",
            # Missing other keys — should default to empty strings
        }
        clause = _make_clause()
        verdict = _make_verdict()
        result = await generate_consequence_chain(clause, verdict)
        assert isinstance(result, ConsequenceChain)
        assert result.trigger_condition == "Some trigger"
        assert result.immediate_consequence == ""

    @pytest.mark.asyncio
    @patch("backend.services.consequence_engine.call_gemini")
    async def test_uses_gemini_pro_model(
        self, mock_gemini: AsyncMock
    ):
        """Consequence engine should use gemini-1.5-pro for quality."""
        mock_gemini.return_value = {
            "trigger_condition": "t",
            "immediate_consequence": "t",
            "downstream_impact": "t",
            "worst_case_scenario": "t",
        }
        clause = _make_clause()
        verdict = _make_verdict()
        await generate_consequence_chain(clause, verdict)
        call_kwargs = mock_gemini.call_args.kwargs
        assert call_kwargs.get("model_name") == "gemini-1.5-pro"
