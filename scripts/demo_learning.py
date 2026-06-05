#!/usr/bin/env python3
"""
Demonstrate learning from operator edits: Run 1 -> edit -> learn -> Run 2 -> report.

Requires:
  - Processed document under data/processed/
  - GEMINI_API_KEY in .env

Usage:
  python scripts/demo_learning.py --doc-id <document_id>
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _run(cmd: list[str]) -> None:
    print(f"\n>> {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run 1 / Run 2 learning demo")
    parser.add_argument("--doc-id", required=True, help="Processed document id")
    args = parser.parse_args()
    doc_id: str = args.doc_id

    _run([sys.executable, "-m", "src", "draft", "--doc-id", doc_id, "--run-label", "run1"])

    drafts_dir = ROOT / "data" / "drafts"
    md_files = sorted(drafts_dir.glob("draft_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not md_files:
        print("No draft markdown found.", file=sys.stderr)
        sys.exit(1)
    latest = md_files[0]
    draft_id = latest.stem.replace(".md", "") if latest.suffix == ".md" else latest.stem
    if not draft_id.startswith("draft_"):
        draft_id = latest.stem

    edited_path = ROOT / "data" / "edits" / "demo_edited.md"
    edited_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "simulate_operator_edits.py"),
            str(latest),
            str(edited_path),
        ]
    )

    json_files = sorted(drafts_dir.glob("draft_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    draft_id = json_files[0].stem if json_files else latest.stem

    _run(
        [
            sys.executable,
            "-m",
            "src",
            "learn",
            "--draft-id",
            draft_id,
            "--edited-file",
            str(edited_path),
        ]
    )

    _run(
        [
            sys.executable,
            "-m",
            "src",
            "draft",
            "--doc-id",
            doc_id,
            "--run-label",
            "run2",
            "--use-learning",
        ]
    )

    _run([sys.executable, "-m", "src", "learning-report", "--doc-id", doc_id])
    print("\nDemo complete. See docs/learning_report.md")


if __name__ == "__main__":
    main()
