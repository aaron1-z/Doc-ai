"""ChromaDB persistent storage for document chunks."""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from src.config import Settings
from src.exceptions import RetrievalError
from src.logging_config import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "document_chunks"
COSINE_SPACE = "cosine"


class ChromaChunkStore:
    """Low-level ChromaDB client for chunk vectors and metadata."""

    def __init__(self, settings: Settings) -> None:
        settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        self._persist_dir = str(settings.chroma_persist_dir)
        try:
            self._client = chromadb.PersistentClient(path=self._persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": COSINE_SPACE},
            )
        except Exception as exc:
            logger.exception("Failed to initialize ChromaDB at %s", self._persist_dir)
            raise RetrievalError(f"Cannot initialize ChromaDB at {self._persist_dir}") from exc
        logger.debug("ChromaDB ready at %s (collection=%s)", self._persist_dir, COLLECTION_NAME)

    @property
    def collection(self) -> Collection:
        return self._collection

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks belonging to a document."""
        try:
            self._collection.delete(where={"doc_id": document_id})
            logger.info("Deleted indexed chunks for document %s", document_id)
        except Exception as exc:
            logger.exception("Chroma delete failed for document %s", document_id)
            raise RetrievalError(f"Failed to delete chunks for document '{document_id}'.") from exc

    def upsert_chunks(
        self,
        *,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Insert or replace chunk vectors."""
        if not ids:
            return
        try:
            self._collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as exc:
            logger.exception("Chroma upsert failed for %s chunk(s)", len(ids))
            raise RetrievalError("Failed to store chunk embeddings in ChromaDB.") from exc

    def query(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        document_id: str | None = None,
    ) -> dict[str, list]:
        """Query the collection; optionally filter by document id."""
        where: dict[str, str] | None = {"doc_id": document_id} if document_id else None
        try:
            return self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            logger.exception("Chroma query failed")
            raise RetrievalError("Semantic search query failed.") from exc
