"""Document ingestion and processing domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.models.common import ProcessingStatus


class ExtractedPage(BaseModel):
    """Text extracted from a single page."""

    page_number: int = Field(ge=1)
    text: str
    extraction_method: str  # e.g. "native", "ocr", "merged"
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)


class StructuredFields(BaseModel):
    """Structured legal-style fields extracted from a document."""

    grantor: str | None = None
    grantee: str | None = None
    legal_description: str | None = None
    parcel_id: str | None = None
    recording_date: str | None = None
    recording_number: str | None = None
    county: str | None = None
    state: str | None = None
    encumbrances: list[str] = Field(default_factory=list)
    additional: dict[str, Any] = Field(default_factory=dict)


class DocumentRecord(BaseModel):
    """Processed document record returned by the extraction pipeline."""

    model_config = ConfigDict(json_schema_extra={"example": {"document_id": "deed_abc123"}})

    document_id: str
    source_path: Path
    pages: list[ExtractedPage] = Field(default_factory=list)
    extraction_method: str = "unknown"
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    mime_type: str | None = None
    page_count: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def doc_id(self) -> str:
        """Alias used by retrieval and generation stages."""
        return self.document_id


class ProcessedDocument(BaseModel):
    """Full output of the document processing stage including chunks."""

    record: DocumentRecord
    structured: StructuredFields
    full_text: str
    status: ProcessingStatus = ProcessingStatus.COMPLETED
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def pages(self) -> list[ExtractedPage]:
        return self.record.pages
