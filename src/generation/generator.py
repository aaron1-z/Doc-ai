"""Grounded draft generation using Gemini."""

from __future__ import annotations

import uuid
from typing import Sequence

from src.config import Settings
from src.exceptions import GenerationError
from src.generation.prompts import build_generation_prompt
from src.generation.interfaces import DraftGenerator
from src.llm.gemini import GeminiClient
from src.logging_config import get_logger
from src.models.draft import DraftOutput, DraftSection, DraftType, EvidenceBundle
from src.models.document import ProcessedDocument
from src.models.learning import LearnedPattern, OperatorPreference

logger = get_logger(__name__)


class GeminiTitleReviewGenerator(DraftGenerator):
    """Generate title review drafts with optional learned pattern injection."""

    def __init__(self, settings: Settings, client: GeminiClient | None = None) -> None:
        self._settings = settings
        self._client = client

    def _get_client(self) -> GeminiClient:
        if self._client is None:
            self._client = GeminiClient(self._settings)
        return self._client

    def generate(
        self,
        doc_id: str,
        processed: ProcessedDocument,
        evidence: Sequence[EvidenceBundle],
        draft_type: DraftType = DraftType.TITLE_REVIEW_SUMMARY,
        learned_patterns: Sequence[LearnedPattern] | None = None,
        preferences: Sequence[OperatorPreference] | None = None,
    ) -> DraftOutput:
        prompt = build_generation_prompt(
            doc_id,
            evidence,
            patterns=learned_patterns,
            preferences=preferences,
        )

        if learned_patterns:
            logger.info(
                "Generating draft for %s with %s learned pattern(s)",
                doc_id,
                len(learned_patterns),
            )

        try:
            markdown = self._get_client().generate_text(prompt)
        except GenerationError:
            raise
        except Exception as exc:
            raise GenerationError(f"Draft generation failed for {doc_id}") from exc

        draft_id = f"draft_{doc_id}_{uuid.uuid4().hex[:8]}"
        sections = _parse_sections(markdown)

        return DraftOutput(
            draft_id=draft_id,
            doc_id=doc_id,
            draft_type=draft_type,
            sections=sections,
            markdown=markdown,
            warnings=[] if learned_patterns else ["Generated without learned operator patterns."],
        )


def _parse_sections(markdown: str) -> list[DraftSection]:
    sections: list[DraftSection] = []
    current_name = "Overview"
    current_lines: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append(
                    DraftSection(name=current_name, content="\n".join(current_lines).strip())
                )
            current_name = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append(DraftSection(name=current_name, content="\n".join(current_lines).strip()))

    return sections or [DraftSection(name="Title Review Summary", content=markdown)]
