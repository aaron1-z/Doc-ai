"""Contracts for edit capture and improvement loop."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from src.models.draft import DraftOutput
from src.models.learning import EditSession, LearnedPattern, OperatorPreference


class EditCapturer(ABC):
    """Record operator changes to a generated draft."""

    @abstractmethod
    def capture(
        self,
        draft: DraftOutput,
        edited_markdown: str,
    ) -> EditSession:
        """Persist original vs edited content."""


class PatternExtractor(ABC):
    """Extract reusable patterns from an edit session."""

    @abstractmethod
    def extract(self, session: EditSession) -> EditSession:
        """Populate patterns and preferences on the session."""


class LearningStore(ABC):
    """Persist and query learned signals for future drafts."""

    @abstractmethod
    def save_session(self, session: EditSession) -> None:
        """Store a completed edit session."""

    @abstractmethod
    def get_patterns(self, doc_id: str | None = None) -> Sequence[LearnedPattern]:
        """Return learned patterns, optionally scoped by document."""

    @abstractmethod
    def get_preferences(self) -> Sequence[OperatorPreference]:
        """Return aggregated operator preferences."""

    @abstractmethod
    def find_similar_sessions(
        self,
        draft_id: str,
        top_k: int = 3,
    ) -> Sequence[EditSession]:
        """Return past edit sessions similar to the current context."""
