"""Logging configuration for CLI and pipeline runs."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from src.config import LogFormat, Settings


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            payload.update(record.extra_fields)
        return json.dumps(payload, default=str)


def setup_logging(settings: Settings | None = None) -> None:
    """Configure root logger according to application settings."""
    from src.config import get_settings

    resolved = settings or get_settings()
    level = getattr(logging, resolved.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    if resolved.log_format == LogFormat.JSON:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root.addHandler(handler)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger."""
    return logging.getLogger(name)
