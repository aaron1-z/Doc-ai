"""Section-aware evidence retrieval for title review drafts."""

from __future__ import annotations

from typing import Sequence

from src.config import Settings
from src.generation.prompts import TITLE_REVIEW_SECTIONS
from src.models.draft import DraftType, EvidenceBundle
from src.retrieval.interfaces import Retriever
from src.retrieval.service import RetrievalService

SECTION_QUERIES: dict[str, str] = {
    "Property Description": "legal description parcel property address land",
    "Chain of Title": "grantor grantee deed conveyance chain of title transfer",
    "Exceptions and Encumbrances": "easement lien mortgage encumbrance exception restriction",
    "Risk Factors": "risk defect cloud on title foreclosure dispute",
    "Recommendations": "recommendation action required curative affidavit recording",
}


class TitleReviewRetriever(Retriever):
    """Retrieve evidence per title review section using semantic search."""

    def __init__(self, retrieval: RetrievalService, settings: Settings) -> None:
        self._retrieval = retrieval
        self._top_k = settings.retrieval_top_k
        self._bundler_settings = settings

    def retrieve(
        self,
        doc_id: str,
        draft_type: DraftType = DraftType.TITLE_REVIEW_SUMMARY,
        section_names: Sequence[str] | None = None,
    ) -> Sequence[EvidenceBundle]:
        from src.generation.evidence import SimpleEvidenceBundler

        bundler = SimpleEvidenceBundler(self._bundler_settings)
        names = list(section_names or TITLE_REVIEW_SECTIONS)
        bundles: list[EvidenceBundle] = []

        for section in names:
            query = SECTION_QUERIES.get(section, section)
            hits = self._retrieval.semantic_search(
                query,
                document_id=doc_id,
                top_k=self._top_k,
            )
            bundle = bundler.bundle_from_search_results(section, hits)
            bundles.append(bundle)

        return bundles
