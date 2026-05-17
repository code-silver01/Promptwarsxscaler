"""
Tests for Layer 6 — Negotiation Suggestion Engine.

Tests suggestion generation, benchmark lookup integration,
error fallback (None return), and output structure validation
with mocked Gemini and Firestore calls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from backend.models.schemas import (
    Clause,
    ClauseCategory,
    NegotiationSuggestion,
)
from backend.services.negotiation_engine import generate_suggestion


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_clause(
    text: str = "The Company retains all rights to any work product.",
) -> Clause:
    """Create a minimal Clause for testing."""
    return Clause(
        id="clause_001",
        text=text,
        section="Intellectual Property",
        category=ClauseCategory.IP_TRANSFER,
    )


# ---------------------------------------------------------------------------
# generate_suggestion
# ---------------------------------------------------------------------------

class TestGenerateSuggestion:
    """Tests for negotiation suggestion generation."""

    @pytest.mark.asyncio
    @patch("backend.services.negotiation_engine.get_user_favorable_benchmark")
    @patch("backend.services.negotiation_engine.call_gemini")
    async def test_returns_negotiation_suggestion_instance(
        self, mock_gemini: AsyncMock, mock_benchmark: AsyncMock
    ):
        """Should return a NegotiationSuggestion on success."""
        mock_benchmark.return_value = {
            "text": "Work product created during working hours belongs to the company."
        }
        mock_gemini.return_value = {
            "suggested_text": "Work product created during working hours is company property.",
            "why_safer": "Limits scope to working hours only.",
        }
        clause = _make_clause()
        result = await generate_suggestion(clause, "IP_TRANSFER")
        assert isinstance(result, NegotiationSuggestion)

    @pytest.mark.asyncio
    @patch("backend.services.negotiation_engine.get_user_favorable_benchmark")
    @patch("backend.services.negotiation_engine.call_gemini")
    async def test_suggestion_fields_populated(
        self, mock_gemini: AsyncMock, mock_benchmark: AsyncMock
    ):
        """All suggestion fields should be populated correctly."""
        mock_benchmark.return_value = {"text": "Benchmark clause text."}
        mock_gemini.return_value = {
            "suggested_text": "Fairer alternative clause text.",
            "why_safer": "This version limits company rights to work hours.",
        }
        clause = _make_clause()
        result = await generate_suggestion(clause, "IP_TRANSFER")
        assert result.original_clause_text == clause.text
        assert result.suggested_alternative_text == "Fairer alternative clause text."
        assert result.why_safer == "This version limits company rights to work hours."

    @pytest.mark.asyncio
    @patch("backend.services.negotiation_engine.get_user_favorable_benchmark")
    @patch("backend.services.negotiation_engine.call_gemini")
    async def test_returns_none_on_gemini_failure(
        self, mock_gemini: AsyncMock, mock_benchmark: AsyncMock
    ):
        """Should return None when Gemini call fails."""
        mock_benchmark.return_value = {"text": "Benchmark text."}
        mock_gemini.side_effect = RuntimeError("Gemini API error")
        clause = _make_clause()
        result = await generate_suggestion(clause, "IP_TRANSFER")
        assert result is None

    @pytest.mark.asyncio
    @patch("backend.services.negotiation_engine.get_user_favorable_benchmark")
    @patch("backend.services.negotiation_engine.call_gemini")
    async def test_returns_none_on_benchmark_failure(
        self, mock_gemini: AsyncMock, mock_benchmark: AsyncMock
    ):
        """Should return None when benchmark lookup fails."""
        mock_benchmark.side_effect = RuntimeError("Firestore error")
        clause = _make_clause()
        result = await generate_suggestion(clause, "IP_TRANSFER")
        assert result is None

    @pytest.mark.asyncio
    @patch("backend.services.negotiation_engine.get_user_favorable_benchmark")
    @patch("backend.services.negotiation_engine.call_gemini")
    async def test_works_without_benchmark(
        self, mock_gemini: AsyncMock, mock_benchmark: AsyncMock
    ):
        """Should still generate suggestion when no benchmark is found."""
        mock_benchmark.return_value = None  # No benchmark available
        mock_gemini.return_value = {
            "suggested_text": "Alternative clause without benchmark.",
            "why_safer": "Removes overly broad language.",
        }
        clause = _make_clause()
        result = await generate_suggestion(clause, "IP_TRANSFER")
        assert isinstance(result, NegotiationSuggestion)
        assert result.suggested_alternative_text == "Alternative clause without benchmark."

    @pytest.mark.asyncio
    @patch("backend.services.negotiation_engine.get_user_favorable_benchmark")
    @patch("backend.services.negotiation_engine.call_gemini")
    async def test_original_clause_text_preserved(
        self, mock_gemini: AsyncMock, mock_benchmark: AsyncMock
    ):
        """Original clause text should be preserved in the suggestion."""
        mock_benchmark.return_value = None
        mock_gemini.return_value = {
            "suggested_text": "Suggested text.",
            "why_safer": "Reason.",
        }
        original_text = "The Company retains all rights to any work product created."
        clause = _make_clause(original_text)
        result = await generate_suggestion(clause, "IP_TRANSFER")
        assert result.original_clause_text == original_text

    @pytest.mark.asyncio
    @patch("backend.services.negotiation_engine.get_user_favorable_benchmark")
    @patch("backend.services.negotiation_engine.call_gemini")
    async def test_benchmark_text_included_in_prompt(
        self, mock_gemini: AsyncMock, mock_benchmark: AsyncMock
    ):
        """Benchmark text should be included in the Gemini prompt."""
        benchmark_text = "Unique benchmark reference text for testing."
        mock_benchmark.return_value = {"text": benchmark_text}
        mock_gemini.return_value = {
            "suggested_text": "Suggested.",
            "why_safer": "Reason.",
        }
        clause = _make_clause()
        await generate_suggestion(clause, "IP_TRANSFER")
        call_args = mock_gemini.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert benchmark_text in prompt

    @pytest.mark.asyncio
    @patch("backend.services.negotiation_engine.get_user_favorable_benchmark")
    @patch("backend.services.negotiation_engine.call_gemini")
    async def test_partial_gemini_response_handled(
        self, mock_gemini: AsyncMock, mock_benchmark: AsyncMock
    ):
        """Partial Gemini response should not raise — missing keys default to empty."""
        mock_benchmark.return_value = None
        mock_gemini.return_value = {
            "suggested_text": "Partial response only.",
            # Missing "why_safer"
        }
        clause = _make_clause()
        result = await generate_suggestion(clause, "NON_COMPETE")
        assert isinstance(result, NegotiationSuggestion)
        assert result.suggested_alternative_text == "Partial response only."
        assert result.why_safer == ""
