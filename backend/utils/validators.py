"""
Input validation utilities for LexGuard One.

Provides file type validation, size checks, MIME type detection
from file header bytes, and text sanitization for LLM inputs.
"""

from __future__ import annotations

import re
from typing import Optional

# Magic bytes for supported file types
_MAGIC_BYTES: dict[str, list[bytes]] = {
    "application/pdf": [b"%PDF"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        b"PK\x03\x04"
    ],
}

# Maximum upload file size in bytes (10 MB)
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024

# Allowed MIME types
ALLOWED_MIME_TYPES: set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# HTML/script tag pattern for sanitization
_HTML_TAG_PATTERN: re.Pattern = re.compile(r"<[^>]+>", re.DOTALL)
_SCRIPT_PATTERN: re.Pattern = re.compile(
    r"<script[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE
)


def detect_mime_type(file_header: bytes) -> Optional[str]:
    """
    Detect MIME type from file header magic bytes.

    Args:
        file_header: First 8+ bytes of the file content.

    Returns:
        Detected MIME type string, or None if unrecognized.
    """
    for mime_type, signatures in _MAGIC_BYTES.items():
        for signature in signatures:
            if file_header[: len(signature)] == signature:
                return mime_type
    return None


def validate_file_size(size_bytes: int) -> tuple[bool, str]:
    """
    Check that file size is within the allowed limit.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Tuple of (is_valid, error_message). Error message is empty if valid.
    """
    if size_bytes <= 0:
        return False, "File is empty (0 bytes)"
    if size_bytes > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        actual_mb = size_bytes / (1024 * 1024)
        return False, (
            f"File size {actual_mb:.1f}MB exceeds maximum "
            f"allowed size of {max_mb:.0f}MB"
        )
    return True, ""


def validate_file_type(
    filename: str, file_header: bytes
) -> tuple[bool, str]:
    """
    Validate file type by both extension and magic bytes.

    Args:
        filename: Original filename with extension.
        file_header: First 8+ bytes of file content for MIME detection.

    Returns:
        Tuple of (is_valid, error_message). Error message is empty if valid.
    """
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed_extensions = {"pdf", "docx"}

    if extension not in allowed_extensions:
        return False, (
            f"Unsupported file extension '.{extension}'. "
            f"Allowed: {', '.join(sorted(allowed_extensions))}"
        )

    detected_mime = detect_mime_type(file_header)
    if detected_mime is None:
        return False, "Unable to detect file type from content"
    if detected_mime not in ALLOWED_MIME_TYPES:
        return False, (
            f"File content type '{detected_mime}' is not supported"
        )

    return True, ""


def sanitize_text_for_llm(text: str) -> str:
    """
    Strip HTML/script tags and normalize whitespace before sending to LLM.

    Args:
        text: Raw text that may contain HTML or script injections.

    Returns:
        Sanitized plain text safe for LLM prompts.
    """
    cleaned = _SCRIPT_PATTERN.sub("", text)
    cleaned = _HTML_TAG_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def validate_upload(
    filename: str,
    file_size: int,
    file_header: bytes,
) -> tuple[bool, str]:
    """
    Run all upload validations: size, type, and MIME check.

    Args:
        filename: Original filename.
        file_size: Size of the uploaded file in bytes.
        file_header: First 8+ bytes of the file content.

    Returns:
        Tuple of (is_valid, error_message).
    """
    size_valid, size_error = validate_file_size(file_size)
    if not size_valid:
        return False, size_error

    type_valid, type_error = validate_file_type(filename, file_header)
    if not type_valid:
        return False, type_error

    return True, ""
