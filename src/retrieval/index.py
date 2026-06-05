"""VectorIndex adapter delegating to :class:`RetrievalService`."""

from __future__ import annotations

from typing import Sequence

from src.models.chunk import Chunk, ChunkMetadata
from src.models.retrieval import SearchResult
from src.retrieval.interfaces import VectorIndex
from src.retrieval.service import RetrievalService


class ChromaVectorIndex(VectorIndex):
    """Pipeline-facing adapter for chunk indexing and search."""

    def __init__(self, retrieval: RetrievalService) -> None:
        self._retrieval = retrieval

    @property
    def retrieval(self) -> RetrievalService:
        return self._retrieval

    def index(self, doc_id: str, chunks: Sequence[Chunk]) -> None:
        self._retrieval.index_document(doc_id, chunks)

    def delete(self, doc_id: str) -> None:
        self._retrieval.store.delete_document(doc_id)

    def search(self, query: str, doc_id: str | None = None, top_k: int = 8) -> Sequence[Chunk]:
        hits = self._retrieval.semantic_search(query, document_id=doc_id, top_k=top_k)
        return [_hit_to_chunk(hit, doc_id) for hit in hits]

    def semantic_search(
        self,
        query: str,
        document_id: str | None = None,
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """Return scored search results (preferred API)."""
        return self._retrieval.semantic_search(
            query,
            document_id=document_id,
            top_k=top_k,
        )


def _hit_to_chunk(hit: SearchResult, default_doc_id: str | None) -> Chunk:
    return Chunk(
        chunk_id=hit.chunk_id,
        text=hit.text,
        metadata=ChunkMetadata(
            doc_id=hit.document_id or default_doc_id or "unknown",
            page=hit.page,
        ),
    )
