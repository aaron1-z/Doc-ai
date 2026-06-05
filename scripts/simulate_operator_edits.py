#!/usr/bin/env python3
"""Apply realistic operator edits to a draft for learning demos."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Allow running as: python scripts/simulate_operator_edits.py <original.md> <output.md>


def simulate_edits(markdown: str) -> str:
    edited = markdown
    edited = re.sub(r"\bOwner\b", "Property Owner", edited)
    edited = re.sub(
        r"(## Risk Factors\n)([\s\S]*?)(\n## )",
        r"\1\2\n\nAdditional detail: Review outstanding liens, survey gaps, and access easements.\n\3",
        edited,
        count=1,
    )
    if "recording date" not in edited.lower():
        edited = edited.replace(
            "## Property Description",
            "## Property Description\n\nRecording date: See county recording records for exact filed date.",
        )
    edited = edited.replace("Grantor", "Grantor (verified)")
    return edited


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scripts/simulate_operator_edits.py <input.md> <output.md>")
        sys.exit(1)
    source = Path(sys.argv[1]).read_text(encoding="utf-8")
    Path(sys.argv[2]).write_text(simulate_edits(source), encoding="utf-8")
    print(f"Wrote edited draft to {sys.argv[2]}")


if __name__ == "__main__":
    main()
