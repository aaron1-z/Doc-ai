"""SQLAlchemy models for the learning store."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from src.config import Settings


class Base(DeclarativeBase):
    pass


class EditSessionRow(Base):
    __tablename__ = "edit_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    draft_id: Mapped[str] = mapped_column(String(128), index=True)
    doc_id: Mapped[str] = mapped_column(String(128), index=True)
    original_markdown: Mapped[str] = mapped_column(Text)
    edited_markdown: Mapped[str] = mapped_column(Text)
    diff_unified: Mapped[str] = mapped_column(Text, default="")
    diff_summary: Mapped[str] = mapped_column(String(512), default="")
    original_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    edited_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    patterns: Mapped[list["LearnedPatternRow"]] = relationship(back_populates="session")
    preferences: Mapped[list["OperatorPreferenceRow"]] = relationship(back_populates="session")


class LearnedPatternRow(Base):
    __tablename__ = "learned_patterns"

    pattern_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("edit_sessions.session_id"), index=True
    )
    doc_id: Mapped[str] = mapped_column(String(128), index=True)
    pattern_type: Mapped[str] = mapped_column(String(64))
    rule: Mapped[str] = mapped_column(Text)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    session: Mapped[EditSessionRow] = relationship(back_populates="patterns")


class OperatorPreferenceRow(Base):
    __tablename__ = "operator_preferences"

    preference_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("edit_sessions.session_id"), index=True
    )
    description: Mapped[str] = mapped_column(Text)
    examples_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    session: Mapped[EditSessionRow] = relationship(back_populates="preferences")


class DraftRunRow(Base):
    __tablename__ = "draft_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    draft_id: Mapped[str] = mapped_column(String(128), index=True)
    doc_id: Mapped[str] = mapped_column(String(128), index=True)
    run_label: Mapped[str] = mapped_column(String(32), index=True)
    used_learning: Mapped[bool] = mapped_column(default=False)
    markdown: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


def create_session_factory(settings: Settings) -> sessionmaker[Session]:
    engine = create_engine(settings.sqlite_url, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
