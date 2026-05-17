"""
Pytest configuration and shared fixtures for LexGuard One tests.
"""

import pytest


@pytest.fixture
def sample_pdf_bytes():
    """Provide minimal PDF bytes for testing."""
    return b"%PDF-1.4 minimal test content"


@pytest.fixture
def sample_docx_bytes():
    """Provide valid DOCX bytes for testing."""
    import io
    from docx import Document
    doc = Document()
    doc.add_paragraph("Section 1. Employment Terms")
    doc.add_paragraph(
        "The Employee agrees to perform all duties as assigned by "
        "the Company including but not limited to software development, "
        "testing, and documentation tasks as required by management."
    )
    doc.add_paragraph("Section 2. Intellectual Property")
    doc.add_paragraph(
        "All work product, inventions, and intellectual property "
        "created by the Employee during the term of employment shall "
        "be the sole and exclusive property of the Company."
    )
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
