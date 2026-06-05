"""Dependency container for pipeline composition (clean architecture)."""

from __future__ import annotations

from dataclasses import dataclass

from src.generation.interfaces import DraftGenerator, GroundingValidator
from src.learning.interfaces import EditCapturer, LearningStore, PatternExtractor
from src.processing.interfaces import (
    DocumentLoader,
    DocumentProcessor,
    StructuredFieldExtractor,
    TextChunker,
)
from src.retrieval.interfaces import EvidenceBundler, Retriever, VectorIndex


@dataclass(frozen=True, slots=True)
class PipelineDependencies:
    """
    Explicit dependencies injected into the orchestrator.

    Implementations are wired at the application boundary (CLI / factory),
    keeping the pipeline dependent only on interfaces.
    """

    loader: DocumentLoader
    processor: DocumentProcessor
    structured_extractor: StructuredFieldExtractor
    chunker: TextChunker
    vector_index: VectorIndex
    retriever: Retriever
    evidence_bundler: EvidenceBundler
    draft_generator: DraftGenerator
    grounding_validator: GroundingValidator
    edit_capturer: EditCapturer
    pattern_extractor: PatternExtractor
    learning_store: LearningStore
