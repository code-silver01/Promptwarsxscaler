"""
Firestore client wrapper for LexGuard One.

Handles connection to Google Firestore for benchmark corpus
storage and retrieval, plus persisted analysis reports.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger("lexguard.firestore_client")

# Module-level client singleton
_firestore_client: Optional[firestore.AsyncClient] = None

# Collection names
BENCHMARK_COLLECTION = "benchmark_clauses"
REPORTS_COLLECTION = "analysis_reports"


def get_firestore_client() -> firestore.AsyncClient:
    """
    Get or create the Firestore async client singleton.

    Returns:
        Configured Firestore async client.

    Raises:
        RuntimeError: If GOOGLE_CLOUD_PROJECT is not set.
    """
    global _firestore_client
    if _firestore_client is None:
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        database = os.environ.get(
            "FIRESTORE_DATABASE", "(default)"
        )
        if not project:
            raise RuntimeError(
                "GOOGLE_CLOUD_PROJECT environment variable must be set"
            )
        _firestore_client = firestore.AsyncClient(
            project=project, database=database
        )
        logger.info(
            json.dumps({
                "service": "firestore_client",
                "operation": "initialize",
                "project": project,
                "database": database,
                "status": "success",
            })
        )
    return _firestore_client


async def get_benchmark_clauses(
    category: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve benchmark clauses from Firestore, optionally filtered.

    Args:
        category: Optional clause category to filter by.

    Returns:
        List of benchmark clause documents.
    """
    client = get_firestore_client()
    collection_ref = client.collection(BENCHMARK_COLLECTION)

    try:
        if category:
            query = collection_ref.where(
                filter=FieldFilter("category", "==", category)
            )
            docs = query.stream()
        else:
            docs = collection_ref.stream()

        results = []
        async for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)

        logger.info(
            json.dumps({
                "service": "firestore_client",
                "operation": "get_benchmark_clauses",
                "category": category,
                "count": len(results),
                "status": "success",
            })
        )
        return results

    except Exception as exc:
        logger.error(
            json.dumps({
                "service": "firestore_client",
                "operation": "get_benchmark_clauses",
                "category": category,
                "status": "error",
                "error": str(exc),
            })
        )
        raise


async def get_user_favorable_benchmark(
    category: str,
) -> Optional[dict[str, Any]]:
    """
    Get the most user-favorable benchmark clause for a category.

    Args:
        category: Clause category to search.

    Returns:
        Most favorable benchmark clause, or None if not found.
    """
    client = get_firestore_client()
    collection_ref = client.collection(BENCHMARK_COLLECTION)

    try:
        query = (
            collection_ref
            .where(filter=FieldFilter("category", "==", category))
            .where(filter=FieldFilter("is_user_favorable", "==", True))
            .limit(1)
        )
        docs = query.stream()
        async for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    except Exception as exc:
        logger.error(
            json.dumps({
                "service": "firestore_client",
                "operation": "get_user_favorable_benchmark",
                "category": category,
                "status": "error",
                "error": str(exc),
            })
        )
        raise


async def save_analysis_report(
    report_data: dict[str, Any],
) -> str:
    """
    Persist an analysis report to Firestore.

    Args:
        report_data: Serialized analysis report dictionary.

    Returns:
        Document ID of the saved report.
    """
    client = get_firestore_client()

    try:
        doc_ref = client.collection(REPORTS_COLLECTION).document()
        await doc_ref.set(report_data)

        logger.info(
            json.dumps({
                "service": "firestore_client",
                "operation": "save_analysis_report",
                "document_id": doc_ref.id,
                "status": "success",
            })
        )
        return doc_ref.id

    except Exception as exc:
        logger.error(
            json.dumps({
                "service": "firestore_client",
                "operation": "save_analysis_report",
                "status": "error",
                "error": str(exc),
            })
        )
        raise


async def seed_benchmark_corpus(
    clauses: list[dict[str, Any]],
) -> int:
    """
    Seed the benchmark corpus in Firestore from a list of clauses.

    Args:
        clauses: List of benchmark clause dictionaries to insert.

    Returns:
        Number of clauses successfully written.
    """
    client = get_firestore_client()
    collection_ref = client.collection(BENCHMARK_COLLECTION)
    count = 0

    try:
        batch = client.batch()
        for clause in clauses:
            doc_ref = collection_ref.document()
            batch.set(doc_ref, clause)
            count += 1
        await batch.commit()

        logger.info(
            json.dumps({
                "service": "firestore_client",
                "operation": "seed_benchmark_corpus",
                "count": count,
                "status": "success",
            })
        )
        return count

    except Exception as exc:
        logger.error(
            json.dumps({
                "service": "firestore_client",
                "operation": "seed_benchmark_corpus",
                "status": "error",
                "error": str(exc),
            })
        )
        raise
