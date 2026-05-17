"""
Pydantic models for all I/O boundaries in LexGuard One.

Defines strict typed schemas for clauses, agent outputs,
benchmark comparisons, risk scores, and final reports.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ClauseCategory(str, Enum):
    """Enumeration of all recognized contract clause categories."""

    IP_TRANSFER = "IP_TRANSFER"
    NON_COMPETE = "NON_COMPETE"
    ARBITRATION = "ARBITRATION"
    AUTO_RENEWAL = "AUTO_RENEWAL"
    LIABILITY_LIMITATION = "LIABILITY_LIMITATION"
    DATA_COLLECTION = "DATA_COLLECTION"
    TERMINATION = "TERMINATION"
    PAYMENT_PENALTY = "PAYMENT_PENALTY"
    INDEMNIFICATION = "INDEMNIFICATION"
    JURISDICTION = "JURISDICTION"
    AMBIGUOUS = "AMBIGUOUS"


class Severity(str, Enum):
    """Risk severity levels assigned by the Verdict Agent."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskTier(str, Enum):
    """Document-level risk tier derived from aggregate score."""

    LOW = "Low Risk"
    MODERATE = "Moderate Risk"
    HIGH = "High Risk"
    CRITICAL = "Critical Risk"


class Clause(BaseModel):
    """A single extracted clause from a legal document."""

    id: str = Field(..., description="Unique clause identifier, e.g. clause_001")
    text: str = Field(..., description="Full text of the clause")
    section: str = Field(
        default="General",
        description="Section heading the clause falls under",
    )
    category: Optional[ClauseCategory] = Field(
        default=None,
        description="Classified category, set after Layer 2",
    )
    raw_span: list[int] = Field(
        default_factory=lambda: [0, 0],
        description="Character offsets [start, end] in the original document",
    )


class RiskAgentOutput(BaseModel):
    """Output from the Risk Agent (Red Team)."""

    risk_position: str = Field(
        ..., description="Adversarial interpretation of the clause"
    )
    key_phrases: list[str] = Field(
        default_factory=list,
        description="Exact phrases that create risk",
    )
    worst_case: str = Field(
        ..., description="Worst-case scenario for the signer"
    )
    reasoning: str = Field(
        default="",
        description="Step-by-step reasoning process of the Risk Agent",
    )


class DefenseAgentOutput(BaseModel):
    """Output from the Defense Agent (Blue Team)."""

    defense_position: str = Field(
        ..., description="Favorable interpretation of the clause"
    )
    favorable_phrases: list[str] = Field(
        default_factory=list,
        description="Phrases that protect the signer",
    )
    best_case: str = Field(
        ..., description="Best-case scenario for the signer"
    )
    reasoning: str = Field(
        default="",
        description="Step-by-step reasoning process of the Defense Agent",
    )


class VerdictAgentOutput(BaseModel):
    """Output from the Verdict Agent (neutral synthesis)."""

    verdict: str = Field(..., description="Synthesized verdict text")
    severity: Severity = Field(..., description="Risk severity level")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score 0.0–1.0"
    )
    risk_category: str = Field(
        ..., description="Risk category label for this clause"
    )
    plain_english: str = Field(
        ..., description="Plain English explanation in 2–3 sentences"
    )
    reasoning: str = Field(
        default="",
        description="Step-by-step reasoning process of the Verdict Agent",
    )


class ConsequenceChain(BaseModel):
    """Real-world consequence chain for high-severity clauses."""

    trigger_condition: str = Field(
        ..., description="What triggers the negative outcome"
    )
    immediate_consequence: str = Field(
        ..., description="What happens immediately"
    )
    downstream_impact: str = Field(
        ..., description="Downstream effects over time"
    )
    worst_case_scenario: str = Field(
        ..., description="Worst possible real-world outcome"
    )


class NegotiationSuggestion(BaseModel):
    """Suggested fairer alternative for a risky clause."""

    original_clause_text: str = Field(
        ..., description="The original risky clause text"
    )
    suggested_alternative_text: str = Field(
        ..., description="Rewritten clause that is fairer"
    )
    why_safer: str = Field(
        ..., description="Explanation of why the alternative is safer"
    )


class BenchmarkComparison(BaseModel):
    """Result of comparing a clause against the benchmark corpus."""

    percentile: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentile of how restrictive this clause is",
    )
    summary: str = Field(
        ...,
        description="Human-readable comparison summary",
    )
    top_matches: list[str] = Field(
        default_factory=list,
        description="Top matching benchmark clause texts",
    )


class ClauseScoreBreakdown(BaseModel):
    """Traceable breakdown of a single clause's risk score."""

    base_severity_score: float = Field(
        ..., description="Severity numeric value (1/2/3)"
    )
    category_weight: float = Field(
        ..., description="Category-specific weight multiplier"
    )
    benchmark_deviation: float = Field(
        ..., description="Benchmark deviation multiplier (0.5–1.5)"
    )
    final_score: float = Field(
        ..., description="Product of all components"
    )


class ClauseReport(BaseModel):
    """Complete analysis report for a single clause."""

    clause: Clause
    category: Optional[ClauseCategory] = None
    severity: Optional[Severity] = None
    confidence: Optional[float] = None
    risk_position: Optional[RiskAgentOutput] = None
    defense_position: Optional[DefenseAgentOutput] = None
    verdict: Optional[VerdictAgentOutput] = None
    plain_english: Optional[str] = None
    consequence_chain: Optional[ConsequenceChain] = None
    benchmark_comparison: Optional[BenchmarkComparison] = None
    negotiation_suggestion: Optional[NegotiationSuggestion] = None
    score_breakdown: Optional[ClauseScoreBreakdown] = None
    vague_qualifiers: list[str] = Field(
        default_factory=list,
        description="Detected vague qualifiers in the clause",
    )


class AggregateScoreBreakdown(BaseModel):
    """Traceable breakdown of the document-level risk score."""

    total_clause_score: float = Field(
        ..., description="Sum of all individual clause scores"
    )
    max_possible_score: float = Field(
        ..., description="Maximum possible score for comparison"
    )
    raw_percentage: float = Field(
        ..., description="Raw percentage before tier mapping"
    )
    clause_count: int = Field(
        ..., description="Total number of scored clauses"
    )


class CategoryHeatmapEntry(BaseModel):
    """Count of flagged clauses for a single category."""

    category: str
    count: int


class AnalysisReport(BaseModel):
    """Complete document analysis report — Layer 8 output."""

    document_type: str = Field(
        ..., description="Detected type of contract"
    )
    total_clauses: int = Field(
        ..., description="Total clauses extracted"
    )
    flagged_clauses: int = Field(
        ..., description="Number of flagged clauses"
    )
    risk_tier: RiskTier = Field(
        ..., description="Document-level risk tier"
    )
    aggregate_risk_score: float = Field(
        ..., description="Aggregate risk score 0–100"
    )
    score_breakdown: AggregateScoreBreakdown = Field(
        ..., description="Traceable score derivation"
    )
    clause_reports: list[ClauseReport] = Field(
        default_factory=list,
        description="Per-clause analysis reports",
    )
    category_heatmap: list[CategoryHeatmapEntry] = Field(
        default_factory=list,
        description="Flagged clause count per category",
    )
    contradictions: list[dict] = Field(
        default_factory=list,
        description="Detected clause contradictions",
    )


class AnalyzeRequest(BaseModel):
    """Request metadata for the analyze endpoint."""

    filename: str
    file_size: int


class ErrorDetail(BaseModel):
    """Structured error response."""

    code: str
    message: str
    clause_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """API error envelope."""

    error: ErrorDetail


class HealthResponse(BaseModel):
    """Health check endpoint response."""

    status: str = "ok"
    version: str = "1.0.0"


class StreamingClauseUpdate(BaseModel):
    """
    Streaming update sent to the frontend as each clause is processed.

    Used with Server-Sent Events to provide real-time progress.
    """

    type: str = Field(
        ...,
        description="Event type: 'progress', 'clause_result', 'complete', 'error'",
    )
    stage: Optional[str] = Field(
        default=None,
        description="Current processing stage name",
    )
    clause_report: Optional[ClauseReport] = None
    report: Optional[AnalysisReport] = None
    error: Optional[ErrorDetail] = None
    progress_percent: Optional[float] = None

    @field_validator("type")
    @classmethod
    def validate_event_type(cls, value: str) -> str:
        """Ensure event type is one of the allowed values."""
        allowed = {"progress", "clause_result", "complete", "error"}
        if value not in allowed:
            raise ValueError(
                f"Event type must be one of {allowed}, got '{value}'"
            )
        return value
