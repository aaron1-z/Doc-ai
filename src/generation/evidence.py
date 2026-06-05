"""Evidence bundling for retrieval hits."""

from __future__ import annotations

from typing import Sequence

from src.config import Settings
from src.models.chunk import Chunk, ChunkMetadata
from src.models.draft import EvidenceBundle
from src.models.document import ProcessedDocument
from src.models.retrieval import SearchResult
from src.retrieval.interfaces import EvidenceBundler


class SimpleEvidenceBundler(EvidenceBundler):
    """Apply score thresholds and package chunks for generation."""

    def __init__(self, settings: Settings) -> None:
        self._min_score = settings.retrieval_min_score

    def bundle(
        self,
        section_name: str,
        chunks: Sequence[Chunk],
        scores: Sequence[float],
        min_score: float,
    ) -> EvidenceBundle:
        threshold = min_score if min_score >= 0 else self._min_score
        paired = [
            (chunk, score)
            for chunk, score in zip(chunks, scores, strict=False)
            if score >= threshold
        ]
        if not paired:
            paired = list(zip(chunks, scores, strict=False))[:3]

        if not paired:
            return EvidenceBundle(
                section_name=section_name,
                chunks=[],
                scores=[],
                abstain=True,
                abstain_reason="No evidence met the minimum score threshold.",
            )

        selected_chunks = [chunk for chunk, _ in paired]
        selected_scores = [score for _, score in paired]
        return EvidenceBundle(
            section_name=section_name,
            chunks=selected_chunks,
            scores=selected_scores,
        )

    def bundle_from_search_results(
        self,
        section_name: str,
        results: Sequence[SearchResult],
    ) -> EvidenceBundle:
        chunks = [
            Chunk(
                chunk_id=hit.chunk_id,
                text=hit.text,
                metadata=ChunkMetadataFromHit(hit),
            )
            for hit in results
        ]
        scores = [hit.score for hit in results]
        return self.bundle(section_name, chunks, scores, self._min_score)

    def build_from_processed(
        self,
        processed: ProcessedDocument,
        draft_type: object,
    ) -> Sequence[EvidenceBundle]:
        raise NotImplementedError("Use TitleReviewRetriever instead.")


def ChunkMetadataFromHit(hit: SearchResult) -> ChunkMetadata:
    return ChunkMetadata(
        doc_id=hit.document_id or "unknown",
        page=hit.page,
    )
