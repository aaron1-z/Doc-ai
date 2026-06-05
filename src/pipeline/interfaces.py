"""Contracts for end-to-end pipeline execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.models.draft import DraftOutput
from src.models.document import ProcessedDocument
from src.models.learning import EditSession


class PipelineRunner(ABC):
    """Run multi-stage document workflows."""

    @abstractmethod
    def process_documents(self, input_path: Path) -> list[ProcessedDocument]:
        """Ingest and process all documents under ``input_path``."""

    @abstractmethod
    def generate_draft(
        self,
        doc_id: str,
        *,
        use_learning: bool = False,
    ) -> DraftOutput:
        """Retrieve evidence and generate a grounded draft."""

    @abstractmethod
    def learn_from_edit(
        self,
        draft_id: str,
        edited_markdown: str,
    ) -> EditSession:
        """Capture operator edit and extract reusable patterns."""

    @abstractmethod
    def run_full(
        self,
        input_path: Path,
        doc_id: str,
        *,
        use_learning: bool = False,
    ) -> DraftOutput:
        """Execute process → draft (and optionally apply learning)."""
