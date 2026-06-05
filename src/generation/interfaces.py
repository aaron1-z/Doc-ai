"""Contracts for grounded draft generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from src.models.draft import DraftOutput, DraftType, EvidenceBundle
from src.models.document import ProcessedDocument
from src.models.learning import LearnedPattern, OperatorPreference


class DraftGenerator(ABC):
    """Generate drafts anchored to retrieved evidence."""

    @abstractmethod
    def generate(
        self,
        doc_id: str,
        processed: ProcessedDocument,
        evidence: Sequence[EvidenceBundle],
        draft_type: DraftType = DraftType.TITLE_REVIEW_SUMMARY,
        learned_patterns: Sequence[LearnedPattern] | None = None,
        preferences: Sequence[OperatorPreference] | None = None,
    ) -> DraftOutput:
        """Produce a grounded draft from evidence bundles."""


class GroundingValidator(ABC):
    """Verify that draft content is supported by evidence."""

    @abstractmethod
    def validate(
        self,
        draft: DraftOutput,
        evidence: Sequence[EvidenceBundle],
    ) -> DraftOutput:
        """Return draft with warnings populated for unsupported claims."""
