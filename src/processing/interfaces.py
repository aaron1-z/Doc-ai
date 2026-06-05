"""Contracts for document ingestion and extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

from src.models.chunk import Chunk
from src.models.document import DocumentRecord, ProcessedDocument, StructuredFields


class DocumentLoader(ABC):
    """Load raw files and produce document records."""

    @abstractmethod
    def discover(self, input_path: Path) -> Sequence[Path]:
        """Return supported file paths under ``input_path``."""

    @abstractmethod
    def load(self, source_path: Path) -> DocumentRecord:
        """Create a document record from a source file."""


class DocumentProcessor(ABC):
    """Extract text and structured data from a document."""

    @abstractmethod
    def process(self, record: DocumentRecord) -> ProcessedDocument:
        """Run full extraction pipeline for one document."""


class StructuredFieldExtractor(ABC):
    """Derive structured fields from processed text."""

    @abstractmethod
    def extract(self, processed: ProcessedDocument) -> StructuredFields:
        """Return structured fields for downstream retrieval."""


class TextChunker(ABC):
    """Split processed documents into retrieval-ready chunks."""

    @abstractmethod
    def chunk(self, processed: ProcessedDocument) -> Sequence[Chunk]:
        """Produce chunks with metadata for indexing."""
