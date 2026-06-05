"""Supported file types and extraction method labels."""

from __future__ import annotations

SUPPORTED_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp", ".bmp"}
)
SUPPORTED_PDF_EXTENSIONS: frozenset[str] = frozenset({".pdf"})
SUPPORTED_EXTENSIONS: frozenset[str] = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS

EXTRACTION_NATIVE = "native"
EXTRACTION_OCR = "ocr"
EXTRACTION_IMAGE = "image"
EXTRACTION_MIXED = "mixed"
