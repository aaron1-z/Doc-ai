"""Compare original and edited draft versions."""

from __future__ import annotations

import difflib

from src.models.learning import EditDiff


def compare_drafts(original: str, edited: str) -> EditDiff:
    """Build a unified diff and change summary."""
    original_lines = original.splitlines(keepends=True)
    edited_lines = edited.splitlines(keepends=True)
    unified = difflib.unified_diff(
        original_lines,
        edited_lines,
        fromfile="original",
        tofile="edited",
        lineterm="",
    )
    unified_text = "\n".join(unified)
    additions = sum(
        1 for line in unified_text.splitlines() if line.startswith("+") and not line.startswith("+++")
    )
    deletions = sum(
        1 for line in unified_text.splitlines() if line.startswith("-") and not line.startswith("---")
    )
    summary = (
        f"{additions} line(s) added, {deletions} line(s) removed"
        if additions or deletions
        else "No line-level changes detected"
    )
    return EditDiff(
        unified_diff=unified_text,
        additions=additions,
        deletions=deletions,
        summary=summary,
    )
