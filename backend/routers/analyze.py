"""
POST /api/analyze endpoint — orchestrates the full analysis pipeline.

Accepts PDF/DOCX uploads, streams clause-by-clause results via SSE,
and returns the final analysis report.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncGenerator

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from backend.models.schemas import (
    ClauseCategory, ClauseReport, ErrorDetail, ErrorResponse,
    Severity, StreamingClauseUpdate,
)
from backend.services.adversarial_engine import analyze_clause, should_analyze
from backend.services.benchmark_rag import compare_clause_to_benchmark
from backend.services.clause_classifier import (
    classify_clauses, detect_contradictions, detect_vague_qualifiers,
)
from backend.services.consequence_engine import generate_consequence_chain
from backend.services.document_parser import parse_document
from backend.services.negotiation_engine import generate_suggestion
from backend.services.report_generator import generate_report
from backend.services.risk_scorer import (
    calculate_aggregate_score, determine_risk_tier, score_clause,
)
from backend.utils.validators import validate_upload

logger = logging.getLogger("lexguard.analyze_router")

router = APIRouter()


def _sse_event(data: dict) -> str:
    """Format a dict as a Server-Sent Event string.

    Args:
        data: Dictionary to serialize.

    Returns:
        SSE formatted string.
    """
    return f"data: {json.dumps(data)}\n\n"


def _progress_event(stage: str, percent: float) -> str:
    """Create a progress SSE event.

    Args:
        stage: Current processing stage name.
        percent: Progress percentage.

    Returns:
        SSE formatted progress event.
    """
    update = StreamingClauseUpdate(
        type="progress", stage=stage, progress_percent=percent,
    )
    return _sse_event(update.model_dump(exclude_none=True))


async def _process_single_clause(
    clause_report: ClauseReport,
) -> ClauseReport:
    """Run adversarial analysis, benchmark, consequence, and negotiation.

    Args:
        clause_report: Partially filled clause report.

    Returns:
        Fully populated clause report.
    """
    clause = clause_report.clause
    category = clause_report.category

    if not should_analyze(clause):
        return clause_report

    try:
        risk_out, defense_out, verdict_out = await analyze_clause(clause)
        clause_report.risk_position = risk_out
        clause_report.defense_position = defense_out
        clause_report.verdict = verdict_out
        clause_report.severity = verdict_out.severity
        clause_report.confidence = verdict_out.confidence
        clause_report.plain_english = verdict_out.plain_english
    except Exception as exc:
        logger.error(json.dumps({
            "service": "analyze_router", "clause_id": clause.id,
            "operation": "adversarial_analysis", "error": str(exc),
        }))
        clause_report.severity = Severity.MEDIUM
        clause_report.confidence = 0.3

    # Benchmark comparison
    if category:
        try:
            benchmark = await compare_clause_to_benchmark(
                clause, category.value,
            )
            clause_report.benchmark_comparison = benchmark
        except Exception as exc:
            logger.error(json.dumps({
                "service": "analyze_router", "clause_id": clause.id,
                "operation": "benchmark", "error": str(exc),
            }))

    # Consequence chain for HIGH severity
    if clause_report.severity == Severity.HIGH and clause_report.verdict:
        try:
            chain = await generate_consequence_chain(
                clause, clause_report.verdict,
            )
            clause_report.consequence_chain = chain
        except Exception as exc:
            logger.error(json.dumps({
                "service": "analyze_router", "clause_id": clause.id,
                "operation": "consequence_chain", "error": str(exc),
            }))

    # Negotiation for HIGH and MEDIUM
    if clause_report.severity in {Severity.HIGH, Severity.MEDIUM} and category:
        try:
            suggestion = await generate_suggestion(clause, category.value)
            clause_report.negotiation_suggestion = suggestion
        except Exception as exc:
            logger.error(json.dumps({
                "service": "analyze_router", "clause_id": clause.id,
                "operation": "negotiation", "error": str(exc),
            }))

    # Score the clause
    if clause_report.severity and category:
        percentile = (
            clause_report.benchmark_comparison.percentile
            if clause_report.benchmark_comparison else 50.0
        )
        clause_report.score_breakdown = score_clause(
            clause_report.severity, category, percentile,
        )

    return clause_report


async def _stream_analysis(
    file_content: bytes, filename: str,
) -> AsyncGenerator[str, None]:
    """Stream the full analysis pipeline as SSE events.

    Args:
        file_content: Raw file bytes.
        filename: Original filename.

    Yields:
        SSE formatted event strings.
    """
    start_time = time.time()

    # Stage 1: Extract clauses
    yield _progress_event("Extracting Clauses", 10)
    try:
        clauses = parse_document(file_content, filename)
    except ValueError as exc:
        yield _sse_event({
            "type": "error",
            "error": {"code": "PARSING_FAILED", "message": str(exc)},
        })
        return

    yield _progress_event("Classifying Clauses", 25)

    # Stage 2: Classify
    try:
        clauses = await classify_clauses(clauses)
    except Exception as exc:
        yield _sse_event({
            "type": "error",
            "error": {"code": "CLASSIFICATION_FAILED", "message": str(exc)},
        })
        return

    # Build initial clause reports
    clause_reports: list[ClauseReport] = []
    for clause in clauses:
        vague = detect_vague_qualifiers(clause.text)
        cr = ClauseReport(
            clause=clause, category=clause.category,
            vague_qualifiers=vague,
        )
        clause_reports.append(cr)

    yield _progress_event("Adversarial Analysis", 40)

    # Stage 3-6: Process clauses (parallel in batches)
    total = len(clause_reports)
    for idx, cr in enumerate(clause_reports):
        try:
            clause_reports[idx] = await _process_single_clause(cr)
        except Exception as exc:
            logger.error(json.dumps({
                "service": "analyze_router",
                "clause_id": cr.clause.id,
                "error": str(exc),
            }))

        progress = 40 + (idx / max(total, 1)) * 45
        yield _sse_event({
            "type": "clause_result",
            "clause_report": clause_reports[idx].model_dump(
                exclude_none=True, mode="json",
            ),
            "progress_percent": round(progress, 1),
        })

    # Stage: Contradiction detection
    yield _progress_event("Detecting Contradictions", 88)
    try:
        contradictions = await detect_contradictions(clauses)
    except Exception:
        contradictions = []

    # Stage 7: Scoring
    yield _progress_event("Calculating Risk Score", 92)
    scored = [
        cr.score_breakdown for cr in clause_reports
        if cr.score_breakdown is not None
    ]
    aggregate_score, score_breakdown = calculate_aggregate_score(scored)
    risk_tier = determine_risk_tier(aggregate_score)

    # Stage 8: Report generation
    yield _progress_event("Generating Report", 97)
    report = generate_report(
        clause_reports, aggregate_score, score_breakdown,
        risk_tier, contradictions,
    )

    duration_ms = (time.time() - start_time) * 1000
    logger.info(json.dumps({
        "service": "analyze_router", "operation": "analyze_complete",
        "duration_ms": round(duration_ms, 2),
        "total_clauses": report.total_clauses,
        "flagged_clauses": report.flagged_clauses,
        "risk_tier": report.risk_tier.value,
    }))

    yield _sse_event({
        "type": "complete",
        "report": report.model_dump(mode="json"),
        "progress_percent": 100,
    })


@router.post("/api/analyze")
async def analyze_document(file: UploadFile = File(...)):
    """Analyze a legal document and stream results via SSE.

    Args:
        file: Uploaded PDF or DOCX file.

    Returns:
        StreamingResponse with SSE events.

    Raises:
        HTTPException: 400 for invalid inputs.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "MISSING_FILENAME", "message": "No filename provided"},
        })

    # Read file content
    file_content = await file.read()

    # Validate upload
    file_header = file_content[:16] if file_content else b""
    is_valid, error_msg = validate_upload(
        file.filename, len(file_content), file_header,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_FILE", "message": error_msg},
        })

    return StreamingResponse(
        _stream_analysis(file_content, file.filename),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
