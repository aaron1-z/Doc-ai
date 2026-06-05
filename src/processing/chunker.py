"""Sliding-window text chunker for retrieval indexing."""

from __future__ import annotations

from typing import Sequence

from src.config import Settings
from src.logging_config import get_logger
from src.models.chunk import Chunk, ChunkMetadata
from src.models.document import ProcessedDocument
from src.processing.interfaces import TextChunker

logger = get_logger(__name__)


class SlidingWindowChunker(TextChunker):
    """Split full document text into overlapping chunks."""

    def __init__(self, settings: Settings) -> None:
        self._chunk_size = settings.chunk_size
        self._overlap = settings.chunk_overlap
        if self._overlap >= self._chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

    def chunk(self, processed: ProcessedDocument) -> Sequence[Chunk]:
        doc_id = processed.record.document_id
        text = processed.full_text
        if not text.strip():
            logger.warning("No text to chunk for document %s", doc_id)
            return []

        stride = self._chunk_size - self._overlap
        chunks: list[Chunk] = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + self._chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                page = self._page_for_offset(processed, start)
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc_id}_chunk_{index:04d}",
                        text=chunk_text,
                        metadata=ChunkMetadata(
                            doc_id=doc_id,
                            page=page,
                            confidence=processed.record.confidence_score,
                            extraction_method=processed.record.extraction_method,
                        ),
                    )
                )
                index += 1
            if end >= len(text):
                break
            start += stride

        logger.info("Created %s chunk(s) for document %s", len(chunks), doc_id)
        return chunks

    @staticmethod
    def _page_for_offset(processed: ProcessedDocument, offset: int) -> int:
        """Map a character offset in full_text to a page number."""
        cursor = 0
        for page in sorted(processed.pages, key=lambda p: p.page_number):
            marker = f"--- Page {page.page_number} ---"
            block = f"{marker}\n{page.text}\n\n"
            cursor += len(block)
            if offset < cursor:
                return page.page_number
        return processed.pages[-1].page_number if processed.pages else 1
