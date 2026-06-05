"""Shared value types."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Citation(BaseModel):
    """Reference to a source chunk used in grounded generation."""

    doc_id: str
    page: int
    chunk_id: str
    excerpt: str | None = None
    score: float | None = Field(default=None, ge=0.0, le=1.0)
