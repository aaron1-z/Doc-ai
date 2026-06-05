"""Operator edit and learning domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class PatternType(str, Enum):
    FACTUAL_CORRECTION = "factual_correction"
    STYLE_PREFERENCE = "style_preference"
    SECTION_EMPHASIS = "section_emphasis"
    TERMINOLOGY = "terminology"


class LearnedPattern(BaseModel):
    """Reusable signal extracted from an operator edit."""

    pattern_id: str
    pattern_type: PatternType
    rule: str
    context: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OperatorPreference(BaseModel):
    """Aggregated preferences applied to future drafts."""

    preference_id: str
    description: str
    examples: list[str] = Field(default_factory=list)


class EditDiff(BaseModel):
    """Structured comparison between original and edited drafts."""

    unified_diff: str
    additions: int = 0
    deletions: int = 0
    summary: str = ""


class EditSession(BaseModel):
    """Captured operator review of a generated draft."""

    session_id: str
    draft_id: str
    doc_id: str
    original_markdown: str
    edited_markdown: str
    diff: EditDiff | None = None
    patterns: list[LearnedPattern] = Field(default_factory=list)
    preferences: list[OperatorPreference] = Field(default_factory=list)
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    original_path: str | None = None
    edited_path: str | None = None


class DraftRun(BaseModel):
    """Tracked draft generation run for before/after comparison."""

    run_id: str
    draft_id: str
    doc_id: str
    run_label: str
    used_learning: bool
    markdown: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
