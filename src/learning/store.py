"""SQLite-backed learning store."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.config import Settings
from src.exceptions import LearningError
from src.learning.database import (
    DraftRunRow,
    EditSessionRow,
    LearnedPatternRow,
    OperatorPreferenceRow,
    create_session_factory,
)
from src.learning.interfaces import LearningStore
from src.logging_config import get_logger
from src.models.learning import (
    DraftRun,
    EditDiff,
    EditSession,
    LearnedPattern,
    OperatorPreference,
    PatternType,
)

logger = get_logger(__name__)


class SqliteLearningStore(LearningStore):
    """Persist edit sessions, patterns, preferences, and draft runs in SQLite."""

    def __init__(self, settings: Settings, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or create_session_factory(settings)

    def save_session(self, session: EditSession) -> None:
        with self._session_factory() as db:
            row = EditSessionRow(
                session_id=session.session_id,
                draft_id=session.draft_id,
                doc_id=session.doc_id,
                original_markdown=session.original_markdown,
                edited_markdown=session.edited_markdown,
                diff_unified=session.diff.unified_diff if session.diff else "",
                diff_summary=session.diff.summary if session.diff else "",
                original_path=session.original_path,
                edited_path=session.edited_path,
                captured_at=session.captured_at,
            )
            db.merge(row)

            for pattern in session.patterns:
                db.merge(
                    LearnedPatternRow(
                        pattern_id=pattern.pattern_id,
                        session_id=session.session_id,
                        doc_id=session.doc_id,
                        pattern_type=pattern.pattern_type.value,
                        rule=pattern.rule,
                        context=pattern.context,
                        confidence=pattern.confidence,
                        created_at=pattern.created_at,
                    )
                )

            for pref in session.preferences:
                db.merge(
                    OperatorPreferenceRow(
                        preference_id=pref.preference_id,
                        session_id=session.session_id,
                        description=pref.description,
                        examples_json=json.dumps(pref.examples),
                        created_at=datetime.now(timezone.utc),
                    )
                )
            db.commit()
        logger.info("Saved learning session %s to SQLite", session.session_id)

    def get_patterns(self, doc_id: str | None = None) -> Sequence[LearnedPattern]:
        with self._session_factory() as db:
            stmt = select(LearnedPatternRow).order_by(LearnedPatternRow.created_at.desc())
            if doc_id:
                stmt = stmt.where(LearnedPatternRow.doc_id == doc_id)
            rows = db.scalars(stmt).all()
            return [_row_to_pattern(row) for row in rows]

    def get_preferences(self) -> Sequence[OperatorPreference]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(OperatorPreferenceRow).order_by(OperatorPreferenceRow.created_at.desc())
            ).all()
            return [_row_to_preference(row) for row in rows]

    def find_similar_sessions(self, draft_id: str, top_k: int = 3) -> Sequence[EditSession]:
        with self._session_factory() as db:
            draft_row = db.scalar(
                select(EditSessionRow).where(EditSessionRow.draft_id == draft_id).limit(1)
            )
            if draft_row is None:
                return []

            stmt = (
                select(EditSessionRow)
                .where(EditSessionRow.doc_id == draft_row.doc_id)
                .order_by(EditSessionRow.captured_at.desc())
                .limit(top_k)
            )
            rows = db.scalars(stmt).all()
            return [_row_to_session(db, row) for row in rows]

    def get_relevant_patterns(
        self,
        doc_id: str,
        *,
        limit: int = 20,
    ) -> list[LearnedPattern]:
        """Return patterns for this document plus global patterns, most recent first."""
        patterns = list(self.get_patterns(doc_id))
        if len(patterns) > limit:
            return patterns[:limit]
        if patterns:
            return patterns[:limit]
        return list(self.get_patterns(None))[:limit]

    def save_draft_run(self, run: DraftRun) -> None:
        with self._session_factory() as db:
            db.merge(
                DraftRunRow(
                    run_id=run.run_id,
                    draft_id=run.draft_id,
                    doc_id=run.doc_id,
                    run_label=run.run_label,
                    used_learning=run.used_learning,
                    markdown=run.markdown,
                    created_at=run.created_at,
                )
            )
            db.commit()

    def get_draft_runs(self, doc_id: str) -> list[DraftRun]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(DraftRunRow)
                .where(DraftRunRow.doc_id == doc_id)
                .order_by(DraftRunRow.created_at.asc())
            ).all()
            return [
                DraftRun(
                    run_id=row.run_id,
                    draft_id=row.draft_id,
                    doc_id=row.doc_id,
                    run_label=row.run_label,
                    used_learning=row.used_learning,
                    markdown=row.markdown,
                    created_at=row.created_at,
                )
                for row in rows
            ]


def _row_to_pattern(row: LearnedPatternRow) -> LearnedPattern:
    return LearnedPattern(
        pattern_id=row.pattern_id,
        pattern_type=PatternType(row.pattern_type),
        rule=row.rule,
        context=row.context,
        confidence=row.confidence,
        created_at=row.created_at,
    )


def _row_to_preference(row: OperatorPreferenceRow) -> OperatorPreference:
    return OperatorPreference(
        preference_id=row.preference_id,
        description=row.description,
        examples=json.loads(row.examples_json or "[]"),
    )


def _row_to_session(db: Session, row: EditSessionRow) -> EditSession:
    patterns = db.scalars(
        select(LearnedPatternRow).where(LearnedPatternRow.session_id == row.session_id)
    ).all()
    preferences = db.scalars(
        select(OperatorPreferenceRow).where(OperatorPreferenceRow.session_id == row.session_id)
    ).all()
    diff = EditDiff(
        unified_diff=row.diff_unified,
        summary=row.diff_summary,
    ) if row.diff_unified else None
    return EditSession(
        session_id=row.session_id,
        draft_id=row.draft_id,
        doc_id=row.doc_id,
        original_markdown=row.original_markdown,
        edited_markdown=row.edited_markdown,
        diff=diff,
        patterns=[_row_to_pattern(p) for p in patterns],
        preferences=[_row_to_preference(p) for p in preferences],
        captured_at=row.captured_at,
        original_path=row.original_path,
        edited_path=row.edited_path,
    )


def create_learning_store(settings: Settings) -> SqliteLearningStore:
    return SqliteLearningStore(settings)
