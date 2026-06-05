"""Retrieval search result models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Single hit returned by semantic search."""

    chunk_id: str
    page: int = Field(ge=1)
    text: str
    score: float = Field(ge=0.0, le=1.0)
    document_id: str | None = None
