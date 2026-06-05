"""Grounded retrieval stage."""

from src.retrieval.chroma_store import ChromaChunkStore
from src.retrieval.embeddings import EmbeddingProvider, SentenceTransformerEmbeddings
from src.retrieval.index import ChromaVectorIndex
from src.retrieval.interfaces import EvidenceBundler, Retriever, VectorIndex
from src.retrieval.service import (
    RetrievalService,
    create_retrieval_service,
    index_document,
    semantic_search,
)

__all__ = [
    "ChromaChunkStore",
    "ChromaVectorIndex",
    "EmbeddingProvider",
    "EvidenceBundler",
    "Retriever",
    "RetrievalService",
    "SentenceTransformerEmbeddings",
    "VectorIndex",
    "create_retrieval_service",
    "index_document",
    "semantic_search",
]
