"""Factory for wiring pipeline dependencies."""

from __future__ import annotations

from src.config import get_settings
from src.generation import (
    BasicGroundingValidator,
    GeminiTitleReviewGenerator,
    SimpleEvidenceBundler,
    TitleReviewRetriever,
)
from src.learning import (
    FileEditCapturer,
    GeminiPatternExtractor,
    SqliteLearningStore,
    create_learning_store,
)
from src.pipeline.dependencies import PipelineDependencies
from src.pipeline.orchestrator import DocumentPipeline
from src.processing import (
    DefaultDocumentProcessor,
    FileDocumentLoader,
    PassthroughStructuredExtractor,
    SlidingWindowChunker,
)
from src.retrieval import ChromaVectorIndex, create_retrieval_service


def create_pipeline() -> DocumentPipeline:
    """Build a fully wired pipeline (processing, retrieval, generation, learning)."""
    settings = get_settings()
    settings.ensure_directories()

    retrieval = create_retrieval_service(settings)
    learning_store = create_learning_store(settings)

    deps = PipelineDependencies(
        loader=FileDocumentLoader(),
        processor=DefaultDocumentProcessor(settings),
        structured_extractor=PassthroughStructuredExtractor(),
        chunker=SlidingWindowChunker(settings),
        vector_index=ChromaVectorIndex(retrieval),
        retriever=TitleReviewRetriever(retrieval, settings),
        evidence_bundler=SimpleEvidenceBundler(settings),
        draft_generator=GeminiTitleReviewGenerator(settings),
        grounding_validator=BasicGroundingValidator(),
        edit_capturer=FileEditCapturer(settings),
        pattern_extractor=GeminiPatternExtractor(settings),
        learning_store=learning_store,
    )
    return DocumentPipeline(deps, settings=settings, learning_store=learning_store)


def create_pipeline_from_dependencies(deps: PipelineDependencies) -> DocumentPipeline:
    """Build a pipeline from an explicit dependency container (for tests)."""
    return DocumentPipeline(deps)
