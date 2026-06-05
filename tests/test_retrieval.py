"""Retrieval layer unit tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.config import Settings, reset_settings_cache
from src.models.chunk import Chunk, ChunkMetadata
from src.retrieval.chroma_store import ChromaChunkStore
from src.retrieval.embeddings import EmbeddingProvider
from src.retrieval.service import RetrievalService, distance_to_score, semantic_search

EMBEDDING_DIM = 384


class FakeEmbeddings(EmbeddingProvider):
    """Deterministic embeddings for tests (no model download)."""

    def __init__(self, model_name: str = "fake-MiniLM") -> None:
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_vectorize(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return _vectorize(query)


def _vectorize(text: str) -> list[float]:
    digest = hashlib.sha256(text.encode()).digest()
    values = [((digest[i % len(digest)] / 255.0) * 2.0 - 1.0) for i in range(EMBEDDING_DIM)]
    norm = sum(v * v for v in values) ** 0.5 or 1.0
    return [v / norm for v in values]


@pytest.fixture
def retrieval_settings(tmp_path: Path) -> Settings:
    reset_settings_cache()
    return Settings(
        chroma_persist_dir=tmp_path / "chroma",
        retrieval_top_k=3,
        embedding_model="all-MiniLM-L6-v2",
    )


@pytest.fixture
def retrieval_service(retrieval_settings: Settings) -> RetrievalService:
    store = ChromaChunkStore(retrieval_settings)
    return RetrievalService(
        embedder=FakeEmbeddings(),
        store=store,
        settings=retrieval_settings,
    )


def _sample_chunks(doc_id: str = "doc_test") -> list[Chunk]:
    return [
        Chunk(
            chunk_id=f"{doc_id}_chunk_0000",
            text="Grantor John Smith conveyed property to Jane Doe in 2020.",
            metadata=ChunkMetadata(doc_id=doc_id, page=1),
        ),
        Chunk(
            chunk_id=f"{doc_id}_chunk_0001",
            text="Parcel ID 123-456 is located in Travis County, Texas.",
            metadata=ChunkMetadata(doc_id=doc_id, page=2),
        ),
        Chunk(
            chunk_id=f"{doc_id}_chunk_0002",
            text="An easement for utility access was recorded in 2015.",
            metadata=ChunkMetadata(doc_id=doc_id, page=3),
        ),
    ]


def test_distance_to_score() -> None:
    assert distance_to_score(0.0) == pytest.approx(1.0)
    assert distance_to_score(1.0) == pytest.approx(0.0)


def test_index_and_semantic_search(retrieval_service: RetrievalService) -> None:
    doc_id = "doc_test"
    chunks = _sample_chunks(doc_id)
    retrieval_service.index_document(doc_id, chunks)

    results = retrieval_service.semantic_search(
        "Who is the grantor?",
        document_id=doc_id,
        top_k=2,
    )
    assert len(results) <= 2
    assert results[0].chunk_id
    assert results[0].page >= 1
    assert results[0].text
    assert 0.0 <= results[0].score <= 1.0


def test_semantic_search_respects_top_k(retrieval_service: RetrievalService) -> None:
    doc_id = "doc_topk"
    retrieval_service.index_document(doc_id, _sample_chunks(doc_id))
    results = retrieval_service.semantic_search("parcel county", document_id=doc_id, top_k=1)
    assert len(results) == 1


def test_reindex_replaces_chunks(retrieval_service: RetrievalService) -> None:
    doc_id = "doc_reindex"
    retrieval_service.index_document(doc_id, _sample_chunks(doc_id)[:1])
    retrieval_service.index_document(doc_id, _sample_chunks(doc_id))
    results = retrieval_service.semantic_search("easement", document_id=doc_id, top_k=5)
    texts = " ".join(hit.text for hit in results)
    assert "easement" in texts.lower()


def test_module_level_semantic_search(retrieval_settings: Settings) -> None:
    from src.retrieval.service import index_document as idx

    doc_id = "doc_module"
    idx(doc_id, _sample_chunks(doc_id), settings=retrieval_settings)
    hits = semantic_search("Travis County", document_id=doc_id, top_k=2, settings=retrieval_settings)
    assert hits
    assert "chunk_id" in hits[0].model_dump()
    assert "page" in hits[0].model_dump()
    assert "text" in hits[0].model_dump()
    assert "score" in hits[0].model_dump()
