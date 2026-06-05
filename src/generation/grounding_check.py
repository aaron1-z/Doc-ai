"""Lightweight post-generation grounding checks."""

from __future__ import annotations

import re
from typing import Sequence

from src.generation.interfaces import GroundingValidator
from src.models.draft import DraftOutput, EvidenceBundle

_CITATION_RE = re.compile(r"\[[\w-]+:\d+:[\w-]+\]")


class BasicGroundingValidator(GroundingValidator):
    """Flag drafts with few or no citations."""

    def validate(
        self,
        draft: DraftOutput,
        evidence: Sequence[EvidenceBundle],
    ) -> DraftOutput:
        citations = _CITATION_RE.findall(draft.markdown)
        warnings = list(draft.warnings)
        if len(citations) < 2:
            warnings.append(
                "Draft contains few explicit citations; verify all claims against evidence."
            )
        abstained = [bundle.section_name for bundle in evidence if bundle.abstain]
        if abstained:
            warnings.append(f"Sections with insufficient evidence: {', '.join(abstained)}")
        return draft.model_copy(update={"warnings": warnings})
