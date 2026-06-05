"""Aggregate page-level extraction into document-level metadata."""

from __future__ import annotations

from src.models.document import ExtractedPage
from src.processing.constants import (
    EXTRACTION_IMAGE,
    EXTRACTION_MIXED,
    EXTRACTION_NATIVE,
    EXTRACTION_OCR,
)


def aggregate_extraction_method(pages: list[ExtractedPage]) -> str:
    """Derive document-level extraction method from page methods."""
    methods = {page.extraction_method for page in pages}
    if len(methods) == 1:
        return next(iter(methods))
    if methods <= {EXTRACTION_NATIVE, EXTRACTION_OCR}:
        return EXTRACTION_MIXED
    if EXTRACTION_IMAGE in methods and len(methods) == 1:
        return EXTRACTION_IMAGE
    return EXTRACTION_MIXED


def aggregate_confidence(pages: list[ExtractedPage]) -> float:
    """Mean page confidence, or 0.0 if no pages."""
    if not pages:
        return 0.0
    return sum(page.confidence for page in pages) / len(pages)


def build_full_text(pages: list[ExtractedPage]) -> str:
    """Concatenate page text with clear page boundaries."""
    parts: list[str] = []
    for page in sorted(pages, key=lambda p: p.page_number):
        header = f"--- Page {page.page_number} ---"
        parts.append(f"{header}\n{page.text}")
    return "\n\n".join(parts)
