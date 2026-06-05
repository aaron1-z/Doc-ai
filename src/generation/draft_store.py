"""Persist generated drafts to disk."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from src.config import Settings
from src.exceptions import GenerationError
from src.logging_config import get_logger
from src.models.draft import DraftOutput

logger = get_logger(__name__)

_ADAPTER = TypeAdapter(DraftOutput)


class DraftStore:
    """Save and load :class:`DraftOutput` artifacts."""

    def __init__(self, settings: Settings) -> None:
        self._dir = settings.drafts_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, draft: DraftOutput) -> Path:
        path = self._dir / f"{draft.draft_id}.json"
        try:
            payload = json.dumps(_ADAPTER.dump_python(draft), indent=2, ensure_ascii=False, default=str)
            path.write_text(payload, encoding="utf-8")
            markdown_path = self._dir / f"{draft.draft_id}.md"
            markdown_path.write_text(draft.markdown, encoding="utf-8")
        except OSError as exc:
            logger.exception("Failed to save draft %s", draft.draft_id)
            raise GenerationError(f"Cannot save draft: {draft.draft_id}") from exc
        logger.info("Saved draft %s", draft.draft_id)
        return path

    def load(self, draft_id: str) -> DraftOutput:
        path = self._dir / f"{draft_id}.json"
        if not path.exists():
            raise GenerationError(f"Draft not found: {draft_id}. Generate a draft first.")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return _ADAPTER.validate_python(data)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise GenerationError(f"Cannot load draft: {draft_id}") from exc
