"""Learning loop unit tests (no live Gemini calls)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.config import Settings, reset_settings_cache
from src.generation.draft_store import DraftStore
from src.learning.diff import compare_drafts
from src.learning.edit_capture import FileEditCapturer
from src.learning.pattern_extract import GeminiPatternExtractor
from src.learning.report import LearningReportGenerator
from src.learning.store import SqliteLearningStore, create_session_factory
from src.models.draft import DraftOutput, DraftSection, DraftType
from src.models.learning import DraftRun, EditSession, PatternType


class FakeGemini:
    def generate_json(self, prompt: str) -> dict[str, Any]:
        return {
            "patterns": [
                {
                    "pattern_type": "terminology",
                    "rule": 'Use "Property Owner" instead of "Owner"',
                    "context": "Operator terminology preference",
                    "confidence": 0.9,
                },
                {
                    "pattern_type": "section_emphasis",
                    "rule": "Expand Risk section with additional detail",
                    "context": "Operator added risk narrative",
                    "confidence": 0.85,
                },
                {
                    "pattern_type": "style_preference",
                    "rule": "Always include recording date when available",
                    "context": "Missing field in original draft",
                    "confidence": 0.88,
                },
            ],
            "preferences": [
                {
                    "description": "Use formal property terminology",
                    "examples": ["Property Owner"],
                }
            ],
        }

    def generate_text(self, prompt: str) -> str:
        return "ok"


@pytest.fixture
def learning_settings(tmp_path: Path) -> Settings:
    reset_settings_cache()
    return Settings(
        data_dir=tmp_path / "data",
        drafts_dir=tmp_path / "data" / "drafts",
        edits_dir=tmp_path / "data" / "edits",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        learning_report_path=tmp_path / "learning_report.md",
        gemini_api_key="test-key",
    )


@pytest.fixture
def store(learning_settings: Settings) -> SqliteLearningStore:
    factory = create_session_factory(learning_settings)
    return SqliteLearningStore(learning_settings, session_factory=factory)


def test_compare_drafts_detects_changes() -> None:
    diff = compare_drafts("Owner: John\n", "Property Owner: John\n")
    assert diff.additions >= 1
    assert "Property Owner" in diff.unified_diff or diff.additions > 0


def test_edit_capture_saves_files(learning_settings: Settings) -> None:
    draft = DraftOutput(
        draft_id="draft_test_001",
        doc_id="doc_test",
        sections=[DraftSection(name="Risk Factors", content="Brief risk note.")],
        markdown="## Risk Factors\nOwner: John Smith\n",
    )
    DraftStore(learning_settings).save(draft)
    capturer = FileEditCapturer(learning_settings)
    session = capturer.capture(
        draft,
        "## Risk Factors\nProperty Owner: John Smith\n\nRecording date: 2020-01-15\n",
    )
    assert session.original_path
    assert session.edited_path
    assert session.diff is not None
    assert Path(session.original_path).exists()


def test_pattern_extractor_and_store(learning_settings: Settings, store: SqliteLearningStore) -> None:
    session = EditSession(
        session_id="edit_test01",
        draft_id="draft_test_001",
        doc_id="doc_test",
        original_markdown="Owner: John",
        edited_markdown="Property Owner: John",
    )
    extractor = GeminiPatternExtractor(learning_settings, client=FakeGemini())  # type: ignore[arg-type]
    session = extractor.extract(session)
    assert len(session.patterns) == 3
    assert session.patterns[0].pattern_type == PatternType.TERMINOLOGY

    store.save_session(session)
    loaded = list(store.get_patterns("doc_test"))
    assert len(loaded) >= 3


def test_learning_report_run_comparison(learning_settings: Settings, store: SqliteLearningStore) -> None:
    store.save_draft_run(
        DraftRun(
            run_id="run1_id",
            draft_id="draft_a",
            doc_id="doc_test",
            run_label="run1",
            used_learning=False,
            markdown="## Risk Factors\nOwner: John\n",
        )
    )
    store.save_draft_run(
        DraftRun(
            run_id="run2_id",
            draft_id="draft_b",
            doc_id="doc_test",
            run_label="run2",
            used_learning=True,
            markdown="## Risk Factors\nProperty Owner: John\nRecording date: 2020-01-15\n",
        )
    )
    path = LearningReportGenerator(store, learning_settings).generate("doc_test")
    text = path.read_text(encoding="utf-8")
    assert "Run 1" in text
    assert "Run 2" in text
    assert "Property Owner" in text or "pattern" in text.lower()
