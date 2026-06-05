"""Application-specific exceptions."""

from __future__ import annotations


class AmbitioError(Exception):
    """Base exception for all application errors."""


class ConfigurationError(AmbitioError):
    """Invalid or missing configuration."""


class DocumentProcessingError(AmbitioError):
    """Document ingestion or extraction failed."""


class RetrievalError(AmbitioError):
    """Retrieval or indexing failed."""


class GenerationError(AmbitioError):
    """Draft generation failed."""


class LearningError(AmbitioError):
    """Edit capture or learning-store operations failed."""


class PipelineError(AmbitioError):
    """Pipeline orchestration failed."""
