"""Prompt templates for grounded title review generation."""

from __future__ import annotations

from typing import Sequence

from src.models.draft import EvidenceBundle
from src.models.learning import LearnedPattern, OperatorPreference

TITLE_REVIEW_SECTIONS: tuple[str, ...] = (
    "Property Description",
    "Chain of Title",
    "Exceptions and Encumbrances",
    "Risk Factors",
    "Recommendations",
)


def build_system_instructions() -> str:
    return (
        "You are a legal document analyst producing a title review summary. "
        "Use ONLY the provided evidence. Cite sources as [doc_id:page:chunk_id]. "
        "If evidence is insufficient, state 'INSUFFICIENT EVIDENCE' for that point. "
        "Do not invent facts."
    )


def format_learned_patterns(
    patterns: Sequence[LearnedPattern],
    preferences: Sequence[OperatorPreference],
) -> str:
    if not patterns and not preferences:
        return ""

    lines = [
        "## Operator-learned preferences (apply to this draft)",
        "",
        "These rules were extracted from prior operator edits. Follow them when consistent with evidence:",
        "",
    ]
    for pattern in patterns:
        lines.append(f"- [{pattern.pattern_type.value}] {pattern.rule}")
        if pattern.context:
            lines.append(f"  Context: {pattern.context}")
    for pref in preferences:
        lines.append(f"- {pref.description}")
        for example in pref.examples[:2]:
            lines.append(f"  Example: {example}")
    lines.append("")
    return "\n".join(lines)


def build_generation_prompt(
    doc_id: str,
    evidence: Sequence[EvidenceBundle],
    patterns: Sequence[LearnedPattern] | None = None,
    preferences: Sequence[OperatorPreference] | None = None,
) -> str:
    sections_text: list[str] = []
    for bundle in evidence:
        if bundle.abstain:
            sections_text.append(f"### {bundle.section_name}\nINSUFFICIENT EVIDENCE\n")
            continue
        chunks_text = []
        for chunk, score in zip(bundle.chunks, bundle.scores or [], strict=False):
            score_str = f"{score:.2f}" if score is not None else "n/a"
            chunks_text.append(
                f"[{chunk.chunk_id}] (page {chunk.metadata.page}, score {score_str})\n{chunk.text}"
            )
        sections_text.append(f"### {bundle.section_name}\n" + "\n\n".join(chunks_text))

    learned_block = format_learned_patterns(patterns or [], preferences or [])

    return (
        f"{build_system_instructions()}\n\n"
        f"{learned_block}"
        f"Document ID: {doc_id}\n\n"
        "Produce a Title Review Summary in Markdown with these sections:\n"
        "- Property Description\n"
        "- Chain of Title\n"
        "- Exceptions and Encumbrances\n"
        "- Risk Factors (expand if operator patterns request it)\n"
        "- Recommendations\n\n"
        "Evidence:\n"
        + "\n".join(sections_text)
    )
