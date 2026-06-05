"""Orchestrates edit capture, pattern extraction, and persistence."""

from __future__ import annotations

from src.config import Settings
from src.learning.edit_capture import FileEditCapturer
from src.learning.interfaces import EditCapturer, LearningStore, PatternExtractor
from src.learning.pattern_extract import GeminiPatternExtractor
from src.learning.store import SqliteLearningStore, create_learning_store
from src.models.draft import DraftOutput
from src.models.learning import EditSession


class LearningService:
    """High-level API for the operator edit learning loop."""

    def __init__(
        self,
        capturer: EditCapturer,
        extractor: PatternExtractor,
        store: LearningStore,
    ) -> None:
        self._capturer = capturer
        self._extractor = extractor
        self._store = store

    def learn_from_edit(
        self,
        draft: DraftOutput,
        edited_markdown: str,
    ) -> EditSession:
        session = self._capturer.capture(draft, edited_markdown)
        session = self._extractor.extract(session)
        self._store.save_session(session)
        return session


def create_learning_service(settings: Settings) -> LearningService:
    capturer = FileEditCapturer(settings)
    extractor = GeminiPatternExtractor(settings)
    store = create_learning_store(settings)
    return LearningService(capturer=capturer, extractor=extractor, store=store)
