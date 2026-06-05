"""Structured field extraction (placeholder until LLM pass is implemented)."""

from __future__ import annotations

from src.models.document import ProcessedDocument, StructuredFields
from src.processing.interfaces import StructuredFieldExtractor


class PassthroughStructuredExtractor(StructuredFieldExtractor):
    """Return empty structured fields; populated in a later milestone."""

    def extract(self, processed: ProcessedDocument) -> StructuredFields:
        return processed.structured
