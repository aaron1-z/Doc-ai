"""Serializable processing artifacts written to disk."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from src.models.chunk import Chunk
from src.models.document import DocumentRecord, StructuredFields


class ProcessedDocumentOutput(BaseModel):
    """JSON schema persisted under ``data/processed/{document_id}.json``."""

    document: DocumentRecord
    chunks: list[Chunk]
    full_text: str
    structured: StructuredFields = Field(default_factory=StructuredFields)
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
