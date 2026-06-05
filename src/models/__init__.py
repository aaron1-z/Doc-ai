"""Domain models shared across pipeline stages."""

from src.models.chunk import Chunk, ChunkMetadata
from src.models.common import Citation, ProcessingStatus
from src.models.document import (
    DocumentRecord,
    ExtractedPage,
    ProcessedDocument,
    StructuredFields,
)
from src.models.processing_output import ProcessedDocumentOutput
from src.models.retrieval import SearchResult
from src.models.draft import DraftOutput, DraftSection, EvidenceBundle, TitleReviewDraft
from src.models.learning import (
    DraftRun,
    EditDiff,
    EditSession,
    LearnedPattern,
    OperatorPreference,
)

__all__ = [
    "Citation",
    "Chunk",
    "ChunkMetadata",
    "DocumentRecord",
    "DraftOutput",
    "DraftSection",
    "DraftRun",
    "EditDiff",
    "EditSession",
    "EvidenceBundle",
    "ExtractedPage",
    "LearnedPattern",
    "OperatorPreference",
    "ProcessedDocument",
    "ProcessedDocumentOutput",
    "ProcessingStatus",
    "SearchResult",
    "StructuredFields",
    "TitleReviewDraft",
]
