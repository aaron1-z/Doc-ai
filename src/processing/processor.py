"""Document processor: PDF native + OCR fallback, images via OCR."""

from __future__ import annotations

from pathlib import Path

from src.config import Settings
from src.exceptions import DocumentProcessingError
from src.logging_config import get_logger
from src.models.common import ProcessingStatus
from src.models.document import DocumentRecord, ExtractedPage, ProcessedDocument, StructuredFields
from src.processing.aggregator import (
    aggregate_confidence,
    aggregate_extraction_method,
    build_full_text,
)
from src.processing.constants import SUPPORTED_IMAGE_EXTENSIONS, SUPPORTED_PDF_EXTENSIONS
from src.processing.interfaces import DocumentProcessor
from src.processing.ocr import OcrEngine
from src.processing.page_extractor import ImagePageExtractor, PdfPageExtractor

logger = get_logger(__name__)


class DefaultDocumentProcessor(DocumentProcessor):
    """Extract text from PDFs and images into a :class:`DocumentRecord`."""

    def __init__(self, settings: Settings) -> None:
        ocr = OcrEngine(settings)
        self._pdf_extractor = PdfPageExtractor(settings, ocr)
        self._image_extractor = ImagePageExtractor(ocr)

    def process(self, record: DocumentRecord) -> ProcessedDocument:
        source_path = record.source_path
        suffix = source_path.suffix.lower()
        logger.info("Processing document %s (%s)", record.document_id, source_path.name)

        try:
            pages = self._extract_pages(source_path, suffix)
        except DocumentProcessingError:
            raise
        except Exception as exc:
            logger.exception("Unexpected error processing %s", source_path)
            raise DocumentProcessingError(f"Failed to process {source_path}") from exc

        extraction_method = aggregate_extraction_method(pages)
        confidence_score = aggregate_confidence(pages)
        full_text = build_full_text(pages)

        status = ProcessingStatus.COMPLETED
        if any(not page.text for page in pages):
            status = ProcessingStatus.PARTIAL
            logger.warning("Document %s has empty page(s)", record.document_id)

        updated_record = record.model_copy(
            update={
                "pages": pages,
                "extraction_method": extraction_method,
                "confidence_score": confidence_score,
                "page_count": len(pages),
            }
        )

        logger.info(
            "Processed %s: %s pages, method=%s, confidence=%.2f",
            record.document_id,
            len(pages),
            extraction_method,
            confidence_score,
        )

        return ProcessedDocument(
            record=updated_record,
            structured=StructuredFields(),
            full_text=full_text,
            status=status,
        )

    def _extract_pages(self, source_path: Path, suffix: str) -> list[ExtractedPage]:
        if suffix in SUPPORTED_PDF_EXTENSIONS:
            return self._pdf_extractor.extract_all(source_path)
        if suffix in SUPPORTED_IMAGE_EXTENSIONS:
            return self._image_extractor.extract(source_path)
        raise DocumentProcessingError(f"Unsupported extension: {suffix}")
