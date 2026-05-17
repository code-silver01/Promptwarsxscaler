"""
Layer 1 — Document Ingestion Service.

Extracts text from PDF and DOCX files, then segments
the content into individual structured clauses.
"""

from __future__ import annotations

import io
import json
import logging
import re
from typing import Optional

import pdfplumber
from docx import Document as DocxDocument

from backend.models.schemas import Clause
from backend.utils.validators import sanitize_text_for_llm

logger = logging.getLogger("lexguard.document_parser")

# Regex patterns for section heading detection
_SECTION_HEADING_PATTERNS: list[re.Pattern] = [
    re.compile(r"^(?:ARTICLE|SECTION|CLAUSE)\s+\d+[.:]\s*(.+)", re.IGNORECASE),
    re.compile(r"^\d+\.\s+([A-Z][A-Za-z\s]+)$"),
    re.compile(r"^[IVXLCDM]+\.\s+(.+)", re.IGNORECASE),
    re.compile(r"^[A-Z][A-Z\s]{3,}$"),
]

# Sentence boundary pattern for clause segmentation
_SENTENCE_BOUNDARY = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z])"
)

# Minimum clause length to filter out noise
_MIN_CLAUSE_LENGTH: int = 30


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text content from a PDF file.

    Args:
        file_content: Raw PDF file bytes.

    Returns:
        Extracted text content as a single string.

    Raises:
        ValueError: If PDF cannot be read or contains no text.
    """
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text.strip())

            if not pages_text:
                raise ValueError("PDF contains no extractable text")

            full_text = "\n\n".join(pages_text)
            logger.info(
                json.dumps({
                    "service": "document_parser",
                    "operation": "extract_text_from_pdf",
                    "page_count": len(pdf.pages),
                    "text_length": len(full_text),
                    "status": "success",
                })
            )
            return full_text

    except ValueError:
        raise
    except Exception as exc:
        logger.error(
            json.dumps({
                "service": "document_parser",
                "operation": "extract_text_from_pdf",
                "status": "error",
                "error": str(exc),
            })
        )
        raise ValueError(f"Failed to extract text from PDF: {exc}")


def extract_text_from_docx(file_content: bytes) -> str:
    """
    Extract text content from a DOCX file.

    Args:
        file_content: Raw DOCX file bytes.

    Returns:
        Extracted text content as a single string.

    Raises:
        ValueError: If DOCX cannot be read or is empty.
    """
    try:
        doc = DocxDocument(io.BytesIO(file_content))
        paragraphs = [
            para.text.strip()
            for para in doc.paragraphs
            if para.text.strip()
        ]

        if not paragraphs:
            raise ValueError("DOCX contains no text content")

        full_text = "\n\n".join(paragraphs)
        logger.info(
            json.dumps({
                "service": "document_parser",
                "operation": "extract_text_from_docx",
                "paragraph_count": len(paragraphs),
                "text_length": len(full_text),
                "status": "success",
            })
        )
        return full_text

    except ValueError:
        raise
    except Exception as exc:
        logger.error(
            json.dumps({
                "service": "document_parser",
                "operation": "extract_text_from_docx",
                "status": "error",
                "error": str(exc),
            })
        )
        raise ValueError(f"Failed to extract text from DOCX: {exc}")




def _detect_section_heading(line: str) -> Optional[str]:
    """
    Check if a line matches any section heading pattern.

    Args:
        line: A single line of text.

    Returns:
        Detected section name or None.
    """
    stripped = line.strip()
    for pattern in _SECTION_HEADING_PATTERNS:
        match = pattern.match(stripped)
        if match:
            groups = match.groups()
            return groups[0].strip() if groups else stripped.strip()
    return None


def _split_into_segments(text: str) -> list[dict]:
    """
    Split text into segments by section headings.

    Args:
        text: Full document text.

    Returns:
        List of dicts with 'section' and 'text' keys.
    """
    lines = text.split("\n")
    segments: list[dict] = []
    current_section = "General"
    current_text_parts: list[str] = []
    current_start = 0

    for line in lines:
        heading = _detect_section_heading(line)
        if heading:
            if current_text_parts:
                combined = " ".join(current_text_parts).strip()
                if combined:
                    segments.append({
                        "section": current_section,
                        "text": combined,
                        "start": current_start,
                    })
            current_section = heading
            current_text_parts = []
            current_start = text.find(line)
        else:
            stripped = line.strip()
            if stripped:
                current_text_parts.append(stripped)

    if current_text_parts:
        combined = " ".join(current_text_parts).strip()
        if combined:
            segments.append({
                "section": current_section,
                "text": combined,
                "start": current_start,
            })

    return segments


def _segment_into_clauses(
    segment_text: str, section: str, start_offset: int
) -> list[dict]:
    """
    Break a text segment into individual clause-level chunks.

    Uses numbered list detection first, then sentence boundary fallback.

    Args:
        segment_text: Text within a single section.
        section: Section heading name.
        start_offset: Character offset in original document.

    Returns:
        List of clause dicts with text, section, and span info.
    """
    # Try numbered clause detection first
    numbered_pattern = re.compile(
        r"(?:^|\n)\s*(?:\d+[.)]\s*|[a-z][.)]\s*|•\s*|[-–]\s*)"
    )
    numbered_parts = numbered_pattern.split(segment_text)
    numbered_parts = [
        p.strip() for p in numbered_parts if p.strip()
    ]

    if len(numbered_parts) > 1:
        return _build_clause_dicts(
            numbered_parts, section, segment_text, start_offset
        )

    # Fallback to sentence boundary detection
    sentences = _SENTENCE_BOUNDARY.split(segment_text)
    clause_chunks: list[str] = []
    current_chunk: list[str] = []

    for sentence in sentences:
        current_chunk.append(sentence.strip())
        combined = " ".join(current_chunk)
        if len(combined) >= 100:
            clause_chunks.append(combined)
            current_chunk = []

    if current_chunk:
        combined = " ".join(current_chunk)
        if clause_chunks and len(combined) < _MIN_CLAUSE_LENGTH:
            clause_chunks[-1] += " " + combined
        else:
            clause_chunks.append(combined)

    return _build_clause_dicts(
        clause_chunks, section, segment_text, start_offset
    )


def _build_clause_dicts(
    parts: list[str],
    section: str,
    full_segment: str,
    base_offset: int,
) -> list[dict]:
    """
    Build clause dictionaries from text parts with span offsets.

    Args:
        parts: List of clause text strings.
        section: Section heading name.
        full_segment: Complete segment text for offset calculation.
        base_offset: Base character offset.

    Returns:
        List of clause dictionaries.
    """
    clauses = []
    for part in parts:
        clean_text = part.strip()
        if len(clean_text) < _MIN_CLAUSE_LENGTH:
            continue
        pos = full_segment.find(clean_text[:30])
        start = base_offset + max(pos, 0)
        end = start + len(clean_text)
        clauses.append({
            "text": clean_text,
            "section": section,
            "raw_span": [start, end],
        })
    return clauses


def parse_document(
    file_content: bytes, filename: str
) -> list[Clause]:
    """
    Parse a document file into structured clauses.

    Main entry point for Layer 1. Extracts text based on file type,
    segments into sections, then breaks into individual clauses.

    Args:
        file_content: Raw file bytes.
        filename: Original filename to determine file type.

    Returns:
        List of structured Clause objects.

    Raises:
        ValueError: If file type is unsupported or parsing fails.
    """
    extension = filename.rsplit(".", 1)[-1].lower()

    if extension == "pdf":
        raw_text = extract_text_from_pdf(file_content)
    elif extension == "docx":
        raw_text = extract_text_from_docx(file_content)

    else:
        raise ValueError(f"Unsupported file type: .{extension}")

    # Segment first (needs newlines intact), then sanitize per-clause
    segments = _split_into_segments(raw_text)

    all_clauses: list[dict] = []
    for segment in segments:
        clause_dicts = _segment_into_clauses(
            segment["text"], segment["section"], segment["start"]
        )
        all_clauses.extend(clause_dicts)

    clauses = [
        Clause(
            id=f"clause_{str(idx + 1).zfill(3)}",
            text=sanitize_text_for_llm(clause_dict["text"]),
            section=clause_dict["section"],
            raw_span=clause_dict["raw_span"],
        )
        for idx, clause_dict in enumerate(all_clauses)
    ]

    logger.info(
        json.dumps({
            "service": "document_parser",
            "operation": "parse_document",
            "filename_extension": extension,
            "total_clauses": len(clauses),
            "total_segments": len(segments),
            "status": "success",
        })
    )

    return clauses
