"""Per-page extraction with native text and OCR fallback."""

from __future__ import annotations

from pathlib import Path

import fitz
from PIL import Image

from src.config import Settings
from src.exceptions import DocumentProcessingError
from src.logging_config import get_logger
from src.models.document import ExtractedPage
from src.processing.constants import EXTRACTION_NATIVE, EXTRACTION_OCR
from src.processing.ocr import OcrEngine
from src.processing.pdf_native import extract_native_page_text, open_pdf, page_to_image_bytes

logger = get_logger(__name__)


class PdfPageExtractor:
    """Extract text from PDF pages using native text or OCR fallback."""

    def __init__(self, settings: Settings, ocr: OcrEngine) -> None:
        self._min_chars = settings.native_text_min_chars
        self._render_scale = settings.ocr_render_scale
        self._ocr = ocr

    def extract_all(self, source_path: Path) -> list[ExtractedPage]:
        """Extract all pages from a PDF."""
        doc = open_pdf(source_path)
        pages: list[ExtractedPage] = []
        try:
            for index in range(doc.page_count):
                page_number = index + 1
                fitz_page = doc.load_page(index)
                pages.append(self._extract_page(fitz_page, page_number))
        finally:
            doc.close()
        if not pages:
            raise DocumentProcessingError(f"PDF contains no pages: {source_path}")
        return pages

    def _extract_page(self, page: fitz.Page, page_number: int) -> ExtractedPage:
        native_text = extract_native_page_text(page)
        if len(native_text) >= self._min_chars:
            logger.debug("Page %s: native extraction (%s chars)", page_number, len(native_text))
            return ExtractedPage(
                page_number=page_number,
                text=native_text,
                extraction_method=EXTRACTION_NATIVE,
                confidence=0.95,
            )

        logger.info(
            "Page %s: native text below threshold (%s < %s), using OCR",
            page_number,
            len(native_text),
            self._min_chars,
        )
        warnings: list[str] = []
        if native_text:
            warnings.append("Native text present but below threshold; replaced with OCR.")

        try:
            png_bytes = page_to_image_bytes(page, self._render_scale)
            ocr_result = self._ocr.extract_from_bytes(png_bytes, page_number=page_number)
        except DocumentProcessingError:
            if native_text:
                warnings.append("OCR failed; falling back to partial native text.")
                return ExtractedPage(
                    page_number=page_number,
                    text=native_text,
                    extraction_method=EXTRACTION_NATIVE,
                    confidence=0.4,
                    warnings=warnings,
                )
            raise

        if not ocr_result.text and native_text:
            warnings.append("OCR returned empty text; using native fallback.")
            return ExtractedPage(
                page_number=page_number,
                text=native_text,
                extraction_method=EXTRACTION_NATIVE,
                confidence=0.4,
                warnings=warnings,
            )

        return ExtractedPage(
            page_number=page_number,
            text=ocr_result.text or native_text,
            extraction_method=EXTRACTION_OCR,
            confidence=ocr_result.confidence,
            warnings=warnings,
        )


class ImagePageExtractor:
    """Extract text from a single image file via OCR."""

    def __init__(self, ocr: OcrEngine) -> None:
        self._ocr = ocr

    def extract(self, source_path: Path) -> list[ExtractedPage]:
        try:
            with Image.open(source_path) as image:
                if image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")
                result = self._ocr.extract_from_image(image, page_number=1)
        except DocumentProcessingError:
            raise
        except Exception as exc:
            logger.exception("Failed to open image: %s", source_path)
            raise DocumentProcessingError(f"Cannot open image: {source_path}") from exc

        from src.processing.constants import EXTRACTION_IMAGE

        return [
            ExtractedPage(
                page_number=1,
                text=result.text,
                extraction_method=EXTRACTION_IMAGE,
                confidence=result.confidence,
                warnings=["No text detected by OCR."] if not result.text else [],
            )
        ]
