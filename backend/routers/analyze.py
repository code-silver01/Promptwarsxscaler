"""
POST /api/analyze endpoint — orchestrates the full analysis pipeline.

Accepts PDF/DOCX uploads, streams clause-by-clause results via SSE,
and returns the final analysis report with enhanced multi-agent debate.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncGenerator

from fastapi import APIRouter, File, HTTPException, UploadFile, Header
from fastapi.responses import StreamingResponse

from backend.models.schemas import (
    ClauseCategory, ClauseReport, ErrorDetail, ErrorResponse,
    Severity, StreamingClauseUpdate,
)
from backend.services.enhanced_adversarial_engine import (
    analyze_clause_with_debate, should_analyze, stream_analysis_events
)
from backend.services.benchmark_rag import compare_clause_to_benchmark, batch_embed_clauses
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
from backend.utils.gcs_client import upload_document, delete_document

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


async def _process_single_clause_enhanced(
    clause_report: ClauseReport,
    signer_profile: dict = None,
    clause_embedding: list[float] | None = None,
) -> ClauseReport:
    """Run enhanced adversarial analysis with multi-agent debate.

    Args:
        clause_report: Partially filled clause report.
        signer_profile: User profile for personalized analysis.
        clause_embedding: Pre-computed clause embedding.

    Returns:
        Fully populated clause report with debate data.
    """
    clause = clause_report.clause
    category = clause_report.category

    if not should_analyze(clause):
        return clause_report

    try:
        # Run enhanced multi-agent debate
        risk_out, defense_out, verdict_out, full_analysis = await analyze_clause_with_debate(
            clause, signer_profile
        )
        
        clause_report.risk_position = risk_out
        clause_report.defense_position = defense_out
        clause_report.verdict = verdict_out
        clause_report.severity = verdict_out.severity
        clause_report.confidence = verdict_out.confidence
        clause_report.plain_english = verdict_out.plain_english
        
        # Store full debate analysis for frontend
        clause_report.debate_analysis = full_analysis
        
    except Exception as exc:
        logger.error(json.dumps({
            "service": "analyze_router", "clause_id": clause.id,
            "operation": "enhanced_adversarial_analysis", "error": str(exc),
        }))
        clause_report.severity = Severity.MEDIUM
        clause_report.confidence = 0.3

    # Benchmark comparison
    if category:
        try:
            benchmark = await compare_clause_to_benchmark(
                clause, category.value, clause_embedding,
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


async def _stream_analysis_enhanced(
    file_content: bytes, 
    filename: str,
    signer_profile: dict = None,
) -> AsyncGenerator[str, None]:
    """Stream the enhanced analysis pipeline as SSE events.

    Args:
        file_content: Raw file bytes.
        filename: Original filename.
        signer_profile: User profile for personalized analysis.

    Yields:
        SSE formatted event strings with debate data.
    """
    start_time = time.time()

    # Upload to GCS for temporary storage (non-blocking, best-effort)
    gcs_uri = await upload_document(file_content, filename)

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

    yield _progress_event("Multi-Agent Debate Analysis", 40)

    # Stage 3-6: Process clauses with enhanced debate (parallel in batches)
    total = len(clause_reports)

    # Pre-compute all clause embeddings in one batch call
    clause_embeddings = await batch_embed_clauses(clauses)

    # Semaphore limits concurrent Gemini calls to avoid rate limits
    semaphore = asyncio.Semaphore(3)  # Reduced for enhanced processing

    async def _process_with_semaphore_enhanced(idx: int, cr: ClauseReport) -> tuple[int, ClauseReport]:
        """Process a clause with enhanced debate and concurrency control."""
        async with semaphore:
            try:
                emb = clause_embeddings.get(cr.clause.id)
                result = await _process_single_clause_enhanced(
                    cr, signer_profile, clause_embedding=emb
                )
            except Exception as exc:
                logger.error(json.dumps({
                    "service": "analyze_router",
                    "clause_id": cr.clause.id,
                    "error": str(exc),
                }))
                result = cr
            return idx, result

    # Run all clauses in parallel
    tasks = [_process_with_semaphore_enhanced(i, cr) for i, cr in enumerate(clause_reports)]
    results = await asyncio.gather(*tasks)

    # Re-order results and stream them with debate data
    for idx, processed_cr in sorted(results, key=lambda x: x[0]):
        clause_reports[idx] = processed_cr
        progress = 40 + (idx / max(total, 1)) * 45
        
        # Stream clause result with debate data
        clause_data = clause_reports[idx].model_dump(exclude_none=True, mode="json")
        
        # Add debate visualization data if available
        if hasattr(processed_cr, 'debate_analysis') and processed_cr.debate_analysis:
            clause_data['debate_data'] = {
                'clauseText': processed_cr.clause.text,
                'riskAgent': {
                    'riskPosition': processed_cr.risk_position.risk_position if processed_cr.risk_position else None,
                    'keyPhrases': processed_cr.risk_position.key_phrases if processed_cr.risk_position else [],
                    'worstCase': processed_cr.risk_position.worst_case if processed_cr.risk_position else None,
                    'reasoning': processed_cr.risk_position.reasoning if processed_cr.risk_position else None,
                },
                'defenseAgent': {
                    'defensePosition': processed_cr.defense_position.defense_position if processed_cr.defense_position else None,
                    'favorablePhrases': processed_cr.defense_position.favorable_phrases if processed_cr.defense_position else [],
                    'bestCase': processed_cr.defense_position.best_case if processed_cr.defense_position else None,
                    'reasoning': processed_cr.defense_position.reasoning if processed_cr.defense_position else None,
                },
                'verdict': {
                    'verdict': processed_cr.verdict.verdict if processed_cr.verdict else None,
                    'severity': processed_cr.verdict.severity.value if processed_cr.verdict else None,
                    'confidence': processed_cr.verdict.confidence if processed_cr.verdict else None,
                    'plainEnglish': processed_cr.verdict.plain_english if processed_cr.verdict else None,
                    'reasoning': processed_cr.verdict.reasoning if processed_cr.verdict else None,
                },
                'rounds': processed_cr.debate_analysis.get('debate_history', []) if hasattr(processed_cr, 'debate_analysis') else [],
                'processingTime': processed_cr.debate_analysis.get('processing_time', 0) if hasattr(processed_cr, 'debate_analysis') else 0,
            }
        
        yield _sse_event({
            "type": "clause_result",
            "clause_report": clause_data,
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
        "service": "analyze_router", "operation": "enhanced_analyze_complete",
        "duration_ms": round(duration_ms, 2),
        "total_clauses": report.total_clauses,
        "flagged_clauses": report.flagged_clauses,
        "risk_tier": report.risk_tier.value,
        "signer_profile_used": bool(signer_profile),
    }))

    yield _sse_event({
        "type": "complete",
        "report": report.model_dump(mode="json"),
        "progress_percent": 100,
    })

    # Clean up GCS temp file
    if gcs_uri:
        await delete_document(gcs_uri)


@router.post("/api/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    x_user_profile: str = Header(None, alias="X-User-Profile")
):
    """Analyze a legal document with enhanced multi-agent debate and stream results via SSE.

    Args:
        file: Uploaded PDF or DOCX file.
        x_user_profile: JSON string of user profile for personalized analysis.

    Returns:
        StreamingResponse with SSE events including debate data.

    Raises:
        HTTPException: 400 for invalid inputs.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "MISSING_FILENAME", "message": "No filename provided"},
        })

    # Parse user profile if provided
    signer_profile = None
    if x_user_profile:
        try:
            signer_profile = json.loads(x_user_profile)
        except json.JSONDecodeError:
            logger.warning("Invalid user profile JSON provided")

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
        _stream_analysis_enhanced(file_content, file.filename, signer_profile),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
