"""Application configuration loaded from environment variables and `.env`."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


class Settings(BaseSettings):
    """Central configuration; override via environment or `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: LogFormat = LogFormat.TEXT

    # Paths
    data_dir: Path = Path("./data")
    processed_dir: Path = Path("./data/processed")
    drafts_dir: Path = Path("./data/drafts")
    edits_dir: Path = Path("./data/edits")
    database_url: str = "sqlite:///./data/ambitio.db"

    # Document processing
    tesseract_cmd: str | None = None
    ocr_language: str = "eng"
    ocr_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    native_text_min_chars: int = Field(default=50, ge=0)
    ocr_render_scale: float = Field(default=2.0, ge=1.0)
    chunk_size: int = Field(default=500, ge=64)
    chunk_overlap: int = Field(default=100, ge=0)

    # Retrieval
    embedding_model: str = "all-MiniLM-L6-v2"
    retrieval_top_k: int = Field(default=8, ge=1)
    retrieval_min_score: float = Field(default=0.35, ge=0.0, le=1.0)
    chroma_persist_dir: Path = Path("./data/chroma")

    # Gemini (pattern extraction + draft generation)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_max_tokens: int = Field(default=4096, ge=256)
    gemini_temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    # Learning
    learning_enabled: bool = True
    learning_similar_edits_k: int = Field(default=3, ge=1)
    learning_report_path: Path = Path("./docs/learning_report.md")

    @field_validator(
        "data_dir",
        "processed_dir",
        "drafts_dir",
        "edits_dir",
        "chroma_persist_dir",
        "learning_report_path",
        mode="before",
    )
    @classmethod
    def _coerce_path(cls, value: str | Path) -> Path:
        return Path(value)

    @property
    def is_development(self) -> bool:
        return self.app_env == AppEnvironment.DEVELOPMENT

    def ensure_directories(self) -> None:
        """Create data directories if they do not exist."""
        for directory in (
            self.data_dir,
            self.processed_dir,
            self.drafts_dir,
            self.edits_dir,
            self.chroma_persist_dir,
            self.learning_report_path.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def sqlite_url(self) -> str:
        """Sync SQLAlchemy URL (strip aiosqlite driver if present)."""
        url = self.database_url
        return url.replace("sqlite+aiosqlite", "sqlite")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


def reset_settings_cache() -> None:
    """Clear settings cache (useful in tests)."""
    get_settings.cache_clear()
