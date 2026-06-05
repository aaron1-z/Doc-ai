"""Text embedding providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

from src.exceptions import RetrievalError
from src.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingProvider(ABC):
    """Generate vector embeddings for chunks and queries."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts (batch)."""

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Embed a single search query."""

    def embed_query_batch(self, queries: list[str]) -> list[list[float]]:
        """Default batch implementation for queries."""
        return self.embed_texts(queries)


class SentenceTransformerEmbeddings(EmbeddingProvider):
    """Local embeddings via sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: object | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_model(self):  # noqa: ANN202
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading embedding model: %s", self._model_name)
                self._model = SentenceTransformer(self._model_name)
            except Exception as exc:
                logger.exception("Failed to load embedding model %s", self._model_name)
                raise RetrievalError(
                    f"Cannot load embedding model '{self._model_name}'. "
                    "Install sentence-transformers and ensure the model can download."
                ) from exc
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            model = self._get_model()
            vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return [vector.tolist() for vector in vectors]
        except RetrievalError:
            raise
        except Exception as exc:
            logger.exception("Embedding batch failed")
            raise RetrievalError("Failed to generate embeddings for document chunks.") from exc

    def embed_query(self, query: str) -> list[float]:
        if not query.strip():
            raise RetrievalError("Search query must not be empty.")
        vectors = self.embed_texts([query])
        return vectors[0]


@lru_cache(maxsize=4)
def get_embedding_provider(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformerEmbeddings:
    """Cached embedding provider factory."""
    return SentenceTransformerEmbeddings(model_name=model_name)


def reset_embedding_provider_cache() -> None:
    """Clear cached embedding models (for tests)."""
    get_embedding_provider.cache_clear()
