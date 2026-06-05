"""Discover and load supported document files."""

from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from typing import Sequence

from src.exceptions import DocumentProcessingError
from src.logging_config import get_logger
from src.models.document import DocumentRecord
from src.processing.constants import SUPPORTED_EXTENSIONS
from src.processing.interfaces import DocumentLoader

logger = get_logger(__name__)


def make_document_id(source_path: Path) -> str:
    """Stable document id from absolute path hash and stem."""
    digest = hashlib.sha256(str(source_path.resolve()).encode()).hexdigest()[:12]
    stem = source_path.stem.replace(" ", "_").lower()[:40]
    return f"{stem}_{digest}"


class FileDocumentLoader(DocumentLoader):
    """Discover PDF and image files; build initial document records."""

    def discover(self, input_path: Path) -> Sequence[Path]:
        input_path = input_path.resolve()
        if not input_path.exists():
            raise DocumentProcessingError(f"Input path does not exist: {input_path}")

        if input_path.is_file():
            return [input_path] if self._is_supported(input_path) else []

        files = sorted(
            path
            for path in input_path.rglob("*")
            if path.is_file() and self._is_supported(path)
        )
        logger.info("Discovered %s supported file(s) under %s", len(files), input_path)
        return files

    def load(self, source_path: Path) -> DocumentRecord:
        source_path = source_path.resolve()
        if not source_path.is_file():
            raise DocumentProcessingError(f"Not a file: {source_path}")
        if not self._is_supported(source_path):
            raise DocumentProcessingError(
                f"Unsupported file type: {source_path.suffix}. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        document_id = make_document_id(source_path)
        mime_type, _ = mimetypes.guess_type(source_path)
        logger.debug("Loaded document record for %s -> %s", source_path.name, document_id)

        return DocumentRecord(
            document_id=document_id,
            source_path=source_path,
            mime_type=mime_type,
        )

    @staticmethod
    def _is_supported(path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_EXTENSIONS
