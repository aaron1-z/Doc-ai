"""Retrieval service: index documents and run semantic search."""

from __future__ import annotations

from typing import Sequence

from src.config import Settings
from src.exceptions import RetrievalError
from src.logging_config import get_logger
from src.models.chunk import Chunk
from src.models.retrieval import SearchResult
from src.retrieval.chroma_store import ChromaChunkStore
from src.retrieval.embeddings import EmbeddingProvider

logger = get_logger(__name__)


def distance_to_score(distance: float) -> float:
    """Convert Chroma cosine distance to a similarity score in [0, 1]."""
    return max(0.0, min(1.0, 1.0 - distance))


class RetrievalService:
    """
    High-level retrieval API.

    Use :meth:`index_document` after processing and :meth:`semantic_search` for queries.
    """

    def __init__(
        self,
        embedder: EmbeddingProvider,
        store: ChromaChunkStore,
        settings: Settings,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._default_top_k = settings.retrieval_top_k

    @property
    def embedder(self) -> EmbeddingProvider:
        return self._embedder

    @property
    def store(self) -> ChromaChunkStore:
        return self._store

    def index_document(self, document_id: str, chunks: Sequence[Chunk]) -> None:
        """
        Generate embeddings for chunks and persist them in ChromaDB.

        Re-indexing replaces all existing chunks for ``document_id``.
        """
        if not document_id.strip():
            raise RetrievalError("document_id must not be empty.")

        chunk_list = list(chunks)
        if not chunk_list:
            logger.warning("No chunks to index for document %s", document_id)
            return

        for chunk in chunk_list:
            if chunk.metadata.doc_id != document_id:
                raise RetrievalError(
                    f"Chunk {chunk.chunk_id} doc_id '{chunk.metadata.doc_id}' "
                    f"does not match document_id '{document_id}'."
                )

        logger.info(
            "Indexing document %s (%s chunks) with model %s",
            document_id,
            len(chunk_list),
            self._embedder.model_name,
        )

        self._store.delete_document(document_id)

        texts = [chunk.text for chunk in chunk_list]
        embeddings = self._embedder.embed_texts(texts)
        metadatas = [
            {
                "doc_id": chunk.metadata.doc_id,
                "page": chunk.metadata.page,
                "chunk_id": chunk.chunk_id,
                "extraction_method": chunk.metadata.extraction_method or "",
                "confidence": chunk.metadata.confidence,
            }
            for chunk in chunk_list
        ]
        ids = [chunk.chunk_id for chunk in chunk_list]

        self._store.upsert_chunks(
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Indexed document %s successfully", document_id)

    def semantic_search(
        self,
        query: str,
        document_id: str | None = None,
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """
        Search indexed chunks by semantic similarity.

        Returns hits with ``chunk_id``, ``page``, ``text``, and ``score``.
        """
        limit = top_k or self._default_top_k
        if limit < 1:
            raise RetrievalError("top_k must be at least 1.")

        query_embedding = self._embedder.embed_query(query)
        raw = self._store.query(
            query_embedding=query_embedding,
            top_k=limit,
            document_id=document_id,
        )

        return self._parse_query_results(raw)

    @staticmethod
    def _parse_query_results(raw: dict[str, list]) -> list[SearchResult]:
        ids = (raw.get("ids") or [[]])[0]
        documents = (raw.get("documents") or [[]])[0]
        metadatas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]

        results: list[SearchResult] = []
        for chunk_id, text, metadata, distance in zip(
            ids, documents, metadatas, distances, strict=True
        ):
            if not text or metadata is None:
                continue
            page = int(metadata.get("page", 1))
            resolved_id = str(metadata.get("chunk_id") or chunk_id)
            score = distance_to_score(float(distance))
            results.append(
                SearchResult(
                    chunk_id=resolved_id,
                    page=page,
                    text=text,
                    score=score,
                    document_id=str(metadata.get("doc_id")) if metadata.get("doc_id") else None,
                )
            )
        return results


def create_retrieval_service(settings: Settings) -> RetrievalService:
    """Factory: wire embedding provider and Chroma store (dependency injection)."""
    from src.retrieval.embeddings import get_embedding_provider

    embedder = get_embedding_provider(settings.embedding_model)
    store = ChromaChunkStore(settings)
    return RetrievalService(embedder=embedder, store=store, settings=settings)


def index_document(
    document_id: str,
    chunks: Sequence[Chunk],
    *,
    settings: Settings | None = None,
) -> None:
    """Index chunks for a document (module-level convenience API)."""
    service = create_retrieval_service(settings or get_settings())
    service.index_document(document_id, chunks)


def semantic_search(
    query: str,
    document_id: str | None = None,
    top_k: int | None = None,
    *,
    settings: Settings | None = None,
) -> list[SearchResult]:
    """Semantic search over indexed chunks (module-level convenience API)."""
    service = create_retrieval_service(settings or get_settings())
    return service.semantic_search(query, document_id=document_id, top_k=top_k)
