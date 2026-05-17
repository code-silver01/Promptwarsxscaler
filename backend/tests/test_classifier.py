"""
Tests for Layer 2 — Clause Classifier.

Tests classification accuracy, vague qualifier detection,
and valid category output using mocked Gemini calls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from backend.models.schemas import Clause, ClauseCategory
from backend.services.clause_classifier import (
    classify_single_clause, classify_clauses,
    detect_vague_qualifiers, detect_contradictions,
)


@pytest.fixture
def ip_clause() -> Clause:
    """Create an IP transfer clause for testing."""
    return Clause(
        id="clause_001",
        text=(
            "The Company retains all rights to any work product, "
            "inventions, and intellectual property created by the "
            "Employee during the term of employment."
        ),
        section="Intellectual Property",
    )


@pytest.fixture
def non_compete_clause() -> Clause:
    """Create a non-compete clause for testing."""
    return Clause(
        id="clause_002",
        text=(
            "The Employee agrees not to engage in any business "
            "that competes with the Company within a 100-mile radius "
            "for a period of 24 months after termination."
        ),
        section="Non-Compete",
    )


@pytest.fixture
def vague_clause() -> Clause:
    """Create a clause with vague qualifiers."""
    return Clause(
        id="clause_003",
        text=(
            "The Company may, at our discretion and without notice, "
            "modify the terms of this agreement at any time as "
            "appropriate and in our opinion necessary."
        ),
        section="General Terms",
    )


class TestVagueQualifiers:
    """Tests for vague qualifier detection."""

    def test_vague_qualifier_detected(self, vague_clause: Clause):
        """Should detect multiple vague qualifiers."""
        qualifiers = detect_vague_qualifiers(vague_clause.text)
        assert len(qualifiers) > 0
        assert "at our discretion" in qualifiers
        assert "without notice" in qualifiers
        assert "at any time" in qualifiers

    def test_no_qualifiers_in_clean_clause(self, ip_clause: Clause):
        """Clean clause should have few or no vague qualifiers."""
        qualifiers = detect_vague_qualifiers(ip_clause.text)
        # IP clause has no vague qualifiers
        assert isinstance(qualifiers, list)
        assert len(qualifiers) == 0


class TestClassification:
    """Tests for clause classification."""

    @pytest.mark.asyncio
    @patch("backend.services.clause_classifier.call_gemini")
    async def test_ip_clause_classified_correctly(
        self, mock_gemini: AsyncMock, ip_clause: Clause
    ):
        """IP clause should be classified as IP_TRANSFER."""
        mock_gemini.return_value = {
            "category": "IP_TRANSFER",
            "confidence": 0.95,
            "reasoning": "Work product assignment clause",
        }
        result = await classify_single_clause(ip_clause)
        assert result.category == ClauseCategory.IP_TRANSFER

    @pytest.mark.asyncio
    @patch("backend.services.clause_classifier.call_gemini")
    async def test_non_compete_clause_classified_correctly(
        self, mock_gemini: AsyncMock, non_compete_clause: Clause
    ):
        """Non-compete clause should be classified correctly."""
        mock_gemini.return_value = {
            "category": "NON_COMPETE",
            "confidence": 0.92,
            "reasoning": "Restrictive covenant",
        }
        result = await classify_single_clause(non_compete_clause)
        assert result.category == ClauseCategory.NON_COMPETE

    @pytest.mark.asyncio
    @patch("backend.services.clause_classifier.call_gemini")
    async def test_classifier_returns_valid_category(
        self, mock_gemini: AsyncMock, ip_clause: Clause
    ):
        """Classifier should always return a valid ClauseCategory."""
        mock_gemini.return_value = {
            "category": "TERMINATION",
            "confidence": 0.8,
            "reasoning": "Test",
        }
        result = await classify_single_clause(ip_clause)
        assert isinstance(result.category, ClauseCategory)

    @pytest.mark.asyncio
    @patch("backend.services.clause_classifier.call_gemini")
    async def test_invalid_category_falls_back(
        self, mock_gemini: AsyncMock, ip_clause: Clause
    ):
        """Invalid category from LLM should fall back to AMBIGUOUS."""
        mock_gemini.return_value = {
            "category": "INVALID_CATEGORY",
            "confidence": 0.5,
            "reasoning": "Test",
        }
        result = await classify_single_clause(ip_clause)
        assert result.category == ClauseCategory.AMBIGUOUS

    @pytest.mark.asyncio
    @patch("backend.services.clause_classifier.call_gemini")
    async def test_gemini_exception_falls_back_to_ambiguous(
        self, mock_gemini: AsyncMock, ip_clause: Clause
    ):
        """Gemini exception should fall back to AMBIGUOUS category."""
        mock_gemini.side_effect = RuntimeError("API error")
        result = await classify_single_clause(ip_clause)
        assert result.category == ClauseCategory.AMBIGUOUS

    @pytest.mark.asyncio
    @patch("backend.services.clause_classifier.call_gemini")
    async def test_classify_clauses_batch_processes_all(
        self, mock_gemini: AsyncMock, ip_clause: Clause, non_compete_clause: Clause
    ):
        """classify_clauses should process all clauses in parallel."""
        mock_gemini.return_value = {
            "category": "IP_TRANSFER",
            "confidence": 0.9,
            "reasoning": "Test",
        }
        results = await classify_clauses([ip_clause, non_compete_clause])
        assert len(results) == 2
        assert all(c.category is not None for c in results)

    @pytest.mark.asyncio
    @patch("backend.services.clause_classifier.call_gemini")
    async def test_classify_clauses_empty_list(self, mock_gemini: AsyncMock):
        """classify_clauses with empty list should return empty list."""
        results = await classify_clauses([])
        assert results == []
        mock_gemini.assert_not_called()


class TestContradictionDetection:
    """Tests for contradiction detection between clause pairs."""

    def test_identify_conflict_pairs_ip_and_non_compete(self):
        """IP_TRANSFER and NON_COMPETE should be identified as a conflict pair."""
        from backend.services.clause_classifier import _identify_conflict_pairs
        ip_clause = Clause(
            id="c1",
            text="All IP belongs to company.",
            section="IP",
            category=ClauseCategory.IP_TRANSFER,
        )
        nc_clause = Clause(
            id="c2",
            text="No competing business allowed.",
            section="NC",
            category=ClauseCategory.NON_COMPETE,
        )
        pairs = _identify_conflict_pairs([ip_clause, nc_clause])
        assert len(pairs) == 1
        assert pairs[0][0].id == "c1"
        assert pairs[0][1].id == "c2"

    def test_identify_conflict_pairs_no_conflicts(self):
        """Clauses with no conflicting categories should return no pairs."""
        from backend.services.clause_classifier import _identify_conflict_pairs
        clause_a = Clause(
            id="c1",
            text="Payment terms.",
            section="Payment",
            category=ClauseCategory.PAYMENT_PENALTY,
        )
        clause_b = Clause(
            id="c2",
            text="Jurisdiction clause.",
            section="Jurisdiction",
            category=ClauseCategory.JURISDICTION,
        )
        pairs = _identify_conflict_pairs([clause_a, clause_b])
        assert len(pairs) == 0

    def test_identify_conflict_pairs_skips_none_category(self):
        """Clauses with None category should be skipped."""
        from backend.services.clause_classifier import _identify_conflict_pairs
        clause_a = Clause(id="c1", text="text", section="s", category=None)
        clause_b = Clause(
            id="c2", text="text", section="s", category=ClauseCategory.NON_COMPETE
        )
        pairs = _identify_conflict_pairs([clause_a, clause_b])
        assert len(pairs) == 0

    @pytest.mark.asyncio
    @patch("backend.services.clause_classifier.call_gemini")
    async def test_detect_contradictions_returns_list(
        self, mock_gemini: AsyncMock
    ):
        """detect_contradictions should return a list."""
        mock_gemini.return_value = {
            "is_contradiction": False,
            "explanation": "No conflict found.",
        }
        ip_clause = Clause(
            id="c1",
            text="All IP belongs to company.",
            section="IP",
            category=ClauseCategory.IP_TRANSFER,
        )
        nc_clause = Clause(
            id="c2",
            text="No competing business allowed.",
            section="NC",
            category=ClauseCategory.NON_COMPETE,
        )
        result = await detect_contradictions([ip_clause, nc_clause])
        assert isinstance(result, list)

    @pytest.mark.asyncio
    @patch("backend.services.clause_classifier.call_gemini")
    async def test_detect_contradictions_found(
        self, mock_gemini: AsyncMock
    ):
        """Detected contradiction should be included in results."""
        mock_gemini.return_value = {
            "is_contradiction": True,
            "explanation": "These clauses conflict on IP ownership.",
        }
        ip_clause = Clause(
            id="c1",
            text="All IP belongs to company.",
            section="IP",
            category=ClauseCategory.IP_TRANSFER,
        )
        nc_clause = Clause(
            id="c2",
            text="No competing business allowed.",
            section="NC",
            category=ClauseCategory.NON_COMPETE,
        )
        result = await detect_contradictions([ip_clause, nc_clause])
        assert len(result) == 1
        assert result[0]["clause_a_id"] == "c1"
        assert result[0]["clause_b_id"] == "c2"
