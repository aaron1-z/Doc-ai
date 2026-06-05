"""Extract reusable patterns from operator edits using Gemini."""

from __future__ import annotations

import uuid
from typing import Any

from src.config import Settings
from src.exceptions import LearningError
from src.learning.interfaces import PatternExtractor
from src.llm.gemini import GeminiClient
from src.logging_config import get_logger
from src.models.learning import (
    EditSession,
    LearnedPattern,
    OperatorPreference,
    PatternType,
)

logger = get_logger(__name__)

_PATTERN_PROMPT = """You are analyzing operator edits to a legal title-review draft.

Compare the ORIGINAL and EDITED versions and the unified DIFF. Extract reusable patterns
the system should apply to FUTURE drafts on similar documents.

Examples of good patterns:
- Terminology: replace "Owner" with "Property Owner"
- Section emphasis: expand the Risk section with more detail
- Required content: always include recording date when available in source documents

Return ONLY valid JSON with this schema:
{{
  "patterns": [
    {{
      "pattern_type": "terminology|style_preference|section_emphasis|factual_correction",
      "rule": "clear imperative instruction for future drafts",
      "context": "brief why or when to apply",
      "confidence": 0.0 to 1.0
    }}
  ],
  "preferences": [
    {{
      "description": "aggregated preference statement",
      "examples": ["short example from the edit"]
    }}
  ]
}}

ORIGINAL:
{original}

EDITED:
{edited}

DIFF SUMMARY: {diff_summary}

UNIFIED DIFF:
{diff}
"""


class GeminiPatternExtractor(PatternExtractor):
    """Use Gemini to extract learned patterns from an edit session."""

    def __init__(self, settings: Settings, client: GeminiClient | None = None) -> None:
        self._settings = settings
        self._client = client

    def _get_client(self) -> GeminiClient:
        if self._client is None:
            self._client = GeminiClient(self._settings)
        return self._client

    def extract(self, session: EditSession) -> EditSession:
        diff = session.diff
        if diff is None:
            from src.learning.diff import compare_drafts

            diff = compare_drafts(session.original_markdown, session.edited_markdown)

        prompt = _PATTERN_PROMPT.format(
            original=session.original_markdown[:12000],
            edited=session.edited_markdown[:12000],
            diff_summary=diff.summary,
            diff=diff.unified_diff[:8000],
        )

        try:
            payload = self._get_client().generate_json(prompt)
        except Exception as exc:
            logger.exception("Pattern extraction failed for session %s", session.session_id)
            raise LearningError("Gemini pattern extraction failed.") from exc

        patterns = _parse_patterns(payload, session)
        preferences = _parse_preferences(payload, session)

        logger.info(
            "Extracted %s pattern(s) and %s preference(s) from session %s",
            len(patterns),
            len(preferences),
            session.session_id,
        )

        return session.model_copy(update={"patterns": patterns, "preferences": preferences, "diff": diff})


def _parse_patterns(payload: dict[str, Any], session: EditSession) -> list[LearnedPattern]:
    raw_patterns = payload.get("patterns") or []
    results: list[LearnedPattern] = []
    for item in raw_patterns:
        if not isinstance(item, dict):
            continue
        pattern_type = _coerce_pattern_type(str(item.get("pattern_type", "style_preference")))
        rule = str(item.get("rule", "")).strip()
        if not rule:
            continue
        results.append(
            LearnedPattern(
                pattern_id=f"pat_{uuid.uuid4().hex[:10]}",
                pattern_type=pattern_type,
                rule=rule,
                context=str(item.get("context") or "").strip() or None,
                confidence=float(item.get("confidence", 0.85)),
            )
        )
    return results


def _parse_preferences(payload: dict[str, Any], session: EditSession) -> list[OperatorPreference]:
    raw_prefs = payload.get("preferences") or []
    results: list[OperatorPreference] = []
    for item in raw_prefs:
        if not isinstance(item, dict):
            continue
        description = str(item.get("description", "")).strip()
        if not description:
            continue
        examples = [str(ex) for ex in item.get("examples") or [] if str(ex).strip()]
        results.append(
            OperatorPreference(
                preference_id=f"pref_{uuid.uuid4().hex[:10]}",
                description=description,
                examples=examples,
            )
        )
    return results


def _coerce_pattern_type(value: str) -> PatternType:
    mapping = {member.value: member for member in PatternType}
    normalized = value.strip().lower().replace(" ", "_")
    return mapping.get(normalized, PatternType.STYLE_PREFERENCE)
