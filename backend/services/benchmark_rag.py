"""
Layer 4 — Benchmark Comparison (RAG Layer).

Compares user clauses against a curated benchmark corpus
using Vertex AI embeddings and cosine similarity scoring.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

import numpy as np

from backend.models.schemas import BenchmarkComparison, Clause
from backend.utils.firestore_client import get_benchmark_clauses

logger = logging.getLogger("lexguard.benchmark_rag")

# Module-level embedding cache
_embedding_cache: dict[str, list[float]] = {}


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Compute embeddings for a batch of texts using Vertex AI.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.
    """
    try:
        from vertexai.language_models import TextEmbeddingModel
        import vertexai

        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
        vertexai.init(project=project, location=location)

        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        embeddings_result = model.get_embeddings(texts)
        return [e.values for e in embeddings_result]
    except Exception as exc:
        logger.error(json.dumps({
            "service": "benchmark_rag", "operation": "get_embeddings_batch",
            "status": "error", "error": str(exc),
        }))
        # Fallback: return zero vectors
        return [[0.0] * 768 for _ in texts]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec_a: First embedding vector.
        vec_b: Second embedding vector.

    Returns:
        Cosine similarity score between -1.0 and 1.0.
    """
    a = np.array(vec_a)
    b = np.array(vec_b)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


async def compare_clause_to_benchmark(
    clause: Clause,
    category: str,
) -> BenchmarkComparison:
    """Compare a clause against benchmark corpus for its category.

    Args:
        clause: The user's clause to compare.
        category: Clause category for benchmark filtering.

    Returns:
        BenchmarkComparison with percentile and summary.
    """
    try:
        benchmarks = await get_benchmark_clauses(category=category)
        if not benchmarks:
            return _default_comparison()

        benchmark_texts = [b.get("text", "") for b in benchmarks]
        all_texts = [clause.text] + benchmark_texts
        embeddings = await get_embeddings_batch(all_texts)

        clause_embedding = embeddings[0]
        benchmark_embeddings = embeddings[1:]

        similarities = [
            cosine_similarity(clause_embedding, be)
            for be in benchmark_embeddings
        ]

        top_indices = sorted(
            range(len(similarities)),
            key=lambda i: similarities[i], reverse=True,
        )[:5]

        # Calculate restrictiveness percentile
        less_restrictive_count = sum(
            1 for b in benchmarks
            if b.get("risk_level", "LOW") == "LOW"
            or b.get("is_user_favorable", False)
        )
        percentile = (less_restrictive_count / max(len(benchmarks), 1)) * 100

        top_matches = [benchmark_texts[i][:100] for i in top_indices]
        summary = (
            f"This clause is more restrictive than "
            f"{percentile:.0f}% of similar clauses in our benchmark."
        )

        logger.info(json.dumps({
            "service": "benchmark_rag", "clause_id": clause.id,
            "category": category, "percentile": round(percentile, 1),
            "status": "success",
        }))

        return BenchmarkComparison(
            percentile=percentile, summary=summary, top_matches=top_matches,
        )
    except Exception as exc:
        logger.error(json.dumps({
            "service": "benchmark_rag", "clause_id": clause.id,
            "status": "error", "error": str(exc),
        }))
        return _default_comparison()


def _default_comparison() -> BenchmarkComparison:
    """Return a default comparison when benchmarks are unavailable.

    Returns:
        Default BenchmarkComparison with 50th percentile.
    """
    return BenchmarkComparison(
        percentile=50.0,
        summary="Benchmark comparison unavailable — using default percentile.",
        top_matches=[],
    )
