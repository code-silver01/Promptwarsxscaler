"""
Tests for Layer 4 — Benchmark RAG Service.

Tests cosine similarity computation, default comparison fallback,
batch embedding, and benchmark comparison logic with mocked
Firestore and Vertex AI calls.
"""

from __future__ import annotations

import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models.schemas import BenchmarkComparison, Clause
from backend.services.benchmark_rag import (
    _default_comparison,
    batch_embed_clauses,
    compare_clause_to_benchmark,
    cosine_similarity,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_clause(idx: int = 1, text: str = "The employee agrees to all terms.") -> Clause:
    """Create a minimal Clause for testing."""
    return Clause(id=f"clause_{idx:03d}", text=text, section="General")


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    """Tests for cosine similarity computation."""

    def test_identical_vectors_return_one(self):
        """Identical vectors should have cosine similarity of 1.0."""
        vec = [1.0, 2.0, 3.0]
        result = cosine_similarity(vec, vec)
        assert abs(result - 1.0) < 1e-6

    def test_orthogonal_vectors_return_zero(self):
        """Orthogonal vectors should have cosine similarity of 0.0."""
        result = cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert abs(result) < 1e-6

    def test_opposite_vectors_return_negative_one(self):
        """Opposite vectors should have cosine similarity of -1.0."""
        result = cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert abs(result - (-1.0)) < 1e-6

    def test_zero_vector_returns_zero(self):
        """Zero vector should return 0.0 (no division by zero)."""
        result = cosine_similarity([0.0, 0.0, 0.0], [1.0, 2.0, 3.0])
        assert result == 0.0

    def test_both_zero_vectors_return_zero(self):
        """Both zero vectors should return 0.0."""
        result = cosine_similarity([0.0, 0.0], [0.0, 0.0])
        assert result == 0.0

    def test_similarity_is_symmetric(self):
        """Cosine similarity should be symmetric: sim(a,b) == sim(b,a)."""
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        assert abs(cosine_similarity(a, b) - cosine_similarity(b, a)) < 1e-9

    def test_result_in_valid_range(self):
        """Cosine similarity should always be in [-1.0, 1.0]."""
        a = [0.5, -0.3, 0.8, 1.2]
        b = [-0.1, 0.9, 0.4, -0.7]
        result = cosine_similarity(a, b)
        assert -1.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# _default_comparison
# ---------------------------------------------------------------------------

class TestDefaultComparison:
    """Tests for the default benchmark comparison fallback."""

    def test_default_comparison_returns_50th_percentile(self):
        """Default comparison should use 50th percentile."""
        result = _default_comparison()
        assert result.percentile == 50.0

    def test_default_comparison_returns_benchmark_comparison(self):
        """Default comparison should return a BenchmarkComparison instance."""
        result = _default_comparison()
        assert isinstance(result, BenchmarkComparison)

    def test_default_comparison_has_empty_top_matches(self):
        """Default comparison should have no top matches."""
        result = _default_comparison()
        assert result.top_matches == []

    def test_default_comparison_has_summary(self):
        """Default comparison should have a non-empty summary."""
        result = _default_comparison()
        assert len(result.summary) > 0


# ---------------------------------------------------------------------------
# batch_embed_clauses
# ---------------------------------------------------------------------------

class TestBatchEmbedClauses:
    """Tests for batch clause embedding."""

    @pytest.mark.asyncio
    @patch("backend.services.benchmark_rag.get_embeddings_batch")
    async def test_batch_embed_returns_dict_keyed_by_clause_id(
        self, mock_embed: AsyncMock
    ):
        """batch_embed_clauses should return a dict keyed by clause id."""
        clauses = [_make_clause(1), _make_clause(2)]
        mock_embed.return_value = [[0.1] * 768, [0.2] * 768]
        result = await batch_embed_clauses(clauses)
        assert "clause_001" in result
        assert "clause_002" in result

    @pytest.mark.asyncio
    @patch("backend.services.benchmark_rag.get_embeddings_batch")
    async def test_batch_embed_empty_clauses_returns_empty_dict(
        self, mock_embed: AsyncMock
    ):
        """Empty clause list should return empty dict without calling embed."""
        result = await batch_embed_clauses([])
        mock_embed.assert_not_called()
        assert result == {}

    @pytest.mark.asyncio
    @patch("backend.services.benchmark_rag.get_embeddings_batch")
    async def test_batch_embed_preserves_embedding_values(
        self, mock_embed: AsyncMock
    ):
        """Embeddings should be correctly mapped to clause ids."""
        clause = _make_clause(1)
        expected_emb = [0.5] * 768
        mock_embed.return_value = [expected_emb]
        result = await batch_embed_clauses([clause])
        assert result["clause_001"] == expected_emb


# ---------------------------------------------------------------------------
# compare_clause_to_benchmark
# ---------------------------------------------------------------------------

class TestCompareClauseToBenchmark:
    """Tests for benchmark comparison logic."""

    @pytest.mark.asyncio
    @patch("backend.services.benchmark_rag.get_benchmark_clauses")
    @patch("backend.services.benchmark_rag.get_embeddings_batch")
    async def test_returns_default_when_no_benchmarks(
        self, mock_embed: AsyncMock, mock_get_benchmarks: AsyncMock
    ):
        """Should return default comparison when no benchmarks exist."""
        mock_get_benchmarks.return_value = []
        clause = _make_clause()
        result = await compare_clause_to_benchmark(clause, "IP_TRANSFER")
        assert result.percentile == 50.0

    @pytest.mark.asyncio
    @patch("backend.services.benchmark_rag.get_benchmark_clauses")
    @patch("backend.services.benchmark_rag.get_embeddings_batch")
    async def test_returns_benchmark_comparison_instance(
        self, mock_embed: AsyncMock, mock_get_benchmarks: AsyncMock
    ):
        """Should return a BenchmarkComparison instance."""
        mock_get_benchmarks.return_value = [
            {"text": "benchmark clause text", "risk_level": "LOW", "is_user_favorable": True}
        ]
        mock_embed.return_value = [[0.1] * 768, [0.2] * 768]
        clause = _make_clause()
        result = await compare_clause_to_benchmark(clause, "IP_TRANSFER")
        assert isinstance(result, BenchmarkComparison)

    @pytest.mark.asyncio
    @patch("backend.services.benchmark_rag.get_benchmark_clauses")
    @patch("backend.services.benchmark_rag.get_embeddings_batch")
    async def test_percentile_within_valid_range(
        self, mock_embed: AsyncMock, mock_get_benchmarks: AsyncMock
    ):
        """Percentile should always be between 0 and 100."""
        mock_get_benchmarks.return_value = [
            {"text": "clause a", "risk_level": "HIGH", "is_user_favorable": False},
            {"text": "clause b", "risk_level": "LOW", "is_user_favorable": True},
        ]
        mock_embed.return_value = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
        clause = _make_clause()
        result = await compare_clause_to_benchmark(clause, "NON_COMPETE")
        assert 0.0 <= result.percentile <= 100.0

    @pytest.mark.asyncio
    @patch("backend.services.benchmark_rag.get_benchmark_clauses")
    async def test_returns_default_on_exception(
        self, mock_get_benchmarks: AsyncMock
    ):
        """Should return default comparison when an exception occurs."""
        mock_get_benchmarks.side_effect = RuntimeError("Firestore unavailable")
        clause = _make_clause()
        result = await compare_clause_to_benchmark(clause, "IP_TRANSFER")
        assert result.percentile == 50.0

    @pytest.mark.asyncio
    @patch("backend.services.benchmark_rag.get_benchmark_clauses")
    @patch("backend.services.benchmark_rag.get_embeddings_batch")
    async def test_uses_provided_clause_embedding(
        self, mock_embed: AsyncMock, mock_get_benchmarks: AsyncMock
    ):
        """Should use pre-computed clause embedding when provided."""
        mock_get_benchmarks.return_value = [
            {"text": "benchmark text", "risk_level": "LOW", "is_user_favorable": True}
        ]
        # Only benchmark embeddings should be fetched (not clause embedding)
        mock_embed.return_value = [[0.3] * 768]
        clause = _make_clause()
        pre_computed_emb = [0.9] * 768
        result = await compare_clause_to_benchmark(
            clause, "IP_TRANSFER", clause_embedding=pre_computed_emb
        )
        assert isinstance(result, BenchmarkComparison)
        # Verify embed was called only for benchmark texts (1 call, not 2)
        mock_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.services.benchmark_rag.get_benchmark_clauses")
    @patch("backend.services.benchmark_rag.get_embeddings_batch")
    async def test_summary_contains_percentile(
        self, mock_embed: AsyncMock, mock_get_benchmarks: AsyncMock
    ):
        """Comparison summary should mention the percentile."""
        mock_get_benchmarks.return_value = [
            {"text": "benchmark clause", "risk_level": "LOW", "is_user_favorable": True}
        ]
        mock_embed.return_value = [[0.1] * 768, [0.2] * 768]
        clause = _make_clause()
        result = await compare_clause_to_benchmark(clause, "IP_TRANSFER")
        assert "%" in result.summary or "percentile" in result.summary.lower() or "benchmark" in result.summary.lower()
