"""Native PDF text extraction via PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz

from src.exceptions import DocumentProcessingError
from src.logging_config import get_logger

logger = get_logger(__name__)


def extract_native_page_text(page: fitz.Page) -> str:
    """Extract plain text from a single PDF page."""
    return page.get_text("text").strip()


def open_pdf(source_path: Path) -> fitz.Document:
    """Open a PDF document, raising a domain error on failure."""
    try:
        return fitz.open(source_path)
    except Exception as exc:
        logger.exception("Failed to open PDF: %s", source_path)
        raise DocumentProcessingError(f"Cannot open PDF: {source_path}") from exc


def page_to_image_bytes(page: fitz.Page, scale: float) -> bytes:
    """Render a PDF page to PNG bytes for OCR."""
    matrix = fitz.Matrix(scale, scale)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    return pixmap.tobytes("png")
