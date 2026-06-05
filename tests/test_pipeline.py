"""Pipeline orchestrator contract tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from src.pipeline.dependencies import PipelineDependencies
from src.pipeline.orchestrator import DocumentPipeline


def _mock_dependencies() -> PipelineDependencies:
    mock = MagicMock()
    return PipelineDependencies(
        loader=mock,
        processor=mock,
        structured_extractor=mock,
        chunker=mock,
        vector_index=mock,
        retriever=mock,
        evidence_bundler=mock,
        draft_generator=mock,
        grounding_validator=mock,
        edit_capturer=mock,
        pattern_extractor=mock,
        learning_store=mock,
    )


def test_process_documents_empty_when_nothing_discovered(tmp_path: Path) -> None:
    mock_loader = MagicMock()
    mock_loader.discover.return_value = []
    deps = _mock_dependencies()
    deps = PipelineDependencies(
        loader=mock_loader,
        processor=deps.processor,
        structured_extractor=deps.structured_extractor,
        chunker=deps.chunker,
        vector_index=deps.vector_index,
        retriever=deps.retriever,
        evidence_bundler=deps.evidence_bundler,
        draft_generator=deps.draft_generator,
        grounding_validator=deps.grounding_validator,
        edit_capturer=deps.edit_capturer,
        pattern_extractor=deps.pattern_extractor,
        learning_store=deps.learning_store,
    )
    pipeline = DocumentPipeline(deps)
    assert pipeline.process_documents(tmp_path) == []
