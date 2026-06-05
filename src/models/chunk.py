"""Chunk models for retrieval indexing."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata attached to each searchable chunk."""

    doc_id: str
    page: int = Field(ge=1)
    section_hint: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_method: str | None = None


class Chunk(BaseModel):
    """Atomic unit stored in the retrieval index."""

    chunk_id: str
    text: str
    metadata: ChunkMetadata
