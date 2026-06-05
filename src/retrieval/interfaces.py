"""Contracts for indexing and evidence retrieval."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from src.models.chunk import Chunk
from src.models.draft import DraftType, EvidenceBundle
from src.models.document import ProcessedDocument


class VectorIndex(ABC):
    """Persist and search document chunks."""

    @abstractmethod
    def index(self, doc_id: str, chunks: Sequence[Chunk]) -> None:
        """Add or replace chunks for a document."""

    @abstractmethod
    def delete(self, doc_id: str) -> None:
        """Remove all chunks for a document."""

    @abstractmethod
    def search(self, query: str, doc_id: str | None = None, top_k: int = 8) -> Sequence[Chunk]:
        """Return top-ranked chunks for a query."""


class Retriever(ABC):
    """Retrieve relevant evidence for drafting tasks."""

    @abstractmethod
    def retrieve(
        self,
        doc_id: str,
        draft_type: DraftType,
        section_names: Sequence[str] | None = None,
    ) -> Sequence[EvidenceBundle]:
        """Return evidence bundles per draft section."""


class EvidenceBundler(ABC):
    """Build inspectable evidence artifacts from retrieval results."""

    @abstractmethod
    def bundle(
        self,
        section_name: str,
        chunks: Sequence[Chunk],
        scores: Sequence[float],
        min_score: float,
    ) -> EvidenceBundle:
        """Apply abstention rules and attach scores."""

    @abstractmethod
    def build_from_processed(
        self,
        processed: ProcessedDocument,
        draft_type: DraftType,
    ) -> Sequence[EvidenceBundle]:
        """Convenience: retrieve and bundle in one step."""
