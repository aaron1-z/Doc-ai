"""Capture and persist operator edits."""

from __future__ import annotations

import uuid
from pathlib import Path

from src.config import Settings
from src.exceptions import LearningError
from src.generation.draft_store import DraftStore
from src.learning.diff import compare_drafts
from src.learning.interfaces import EditCapturer
from src.logging_config import get_logger
from src.models.draft import DraftOutput
from src.models.learning import EditSession

logger = get_logger(__name__)


class FileEditCapturer(EditCapturer):
    """Save original and edited drafts to disk and build an edit session."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._draft_store = DraftStore(settings)
        self._edits_dir = settings.edits_dir
        self._edits_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, draft: DraftOutput, edited_markdown: str) -> EditSession:
        if not edited_markdown.strip():
            raise LearningError("Edited markdown must not be empty.")

        session_id = f"edit_{uuid.uuid4().hex[:12]}"
        session_dir = self._edits_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        original_path = session_dir / "original.md"
        edited_path = session_dir / "edited.md"
        diff_path = session_dir / "diff.patch"

        original_path.write_text(draft.markdown, encoding="utf-8")
        edited_path.write_text(edited_markdown, encoding="utf-8")

        diff = compare_drafts(draft.markdown, edited_markdown)
        diff_path.write_text(diff.unified_diff, encoding="utf-8")

        logger.info(
            "Captured edit session %s for draft %s (%s)",
            session_id,
            draft.draft_id,
            diff.summary,
        )

        return EditSession(
            session_id=session_id,
            draft_id=draft.draft_id,
            doc_id=draft.doc_id,
            original_markdown=draft.markdown,
            edited_markdown=edited_markdown,
            diff=diff,
            original_path=str(original_path),
            edited_path=str(edited_path),
        )

    def load_draft(self, draft_id: str) -> DraftOutput:
        return self._draft_store.load(draft_id)
