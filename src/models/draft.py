"""Draft generation and evidence models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from src.models.chunk import Chunk
from src.models.common import Citation


class DraftType(str, Enum):
    TITLE_REVIEW_SUMMARY = "title_review_summary"


class EvidenceBundle(BaseModel):
    """Retrieved evidence for a single draft section."""

    section_name: str
    chunks: list[Chunk]
    scores: list[float] = Field(default_factory=list)
    abstain: bool = False
    abstain_reason: str | None = None


class DraftSection(BaseModel):
    """One section of a generated draft."""

    name: str
    content: str
    citations: list[Citation] = Field(default_factory=list)
    evidence: EvidenceBundle | None = None


class DraftOutput(BaseModel):
    """Complete draft artifact with grounding metadata."""

    draft_id: str
    doc_id: str
    draft_type: DraftType = DraftType.TITLE_REVIEW_SUMMARY
    sections: list[DraftSection]
    markdown: str
    evidence_path: Path | None = None
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TitleReviewDraft(DraftOutput):
    """Specialized draft for title review summaries."""

    draft_type: DraftType = DraftType.TITLE_REVIEW_SUMMARY
