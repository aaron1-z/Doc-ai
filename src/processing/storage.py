"""Persist processed documents to JSON."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from src.config import Settings
from src.exceptions import DocumentProcessingError
from src.logging_config import get_logger
from src.models.chunk import Chunk
from src.models.document import ProcessedDocument, StructuredFields
from src.models.processing_output import ProcessedDocumentOutput

logger = get_logger(__name__)

_OUTPUT_ADAPTER = TypeAdapter(ProcessedDocumentOutput)


class ProcessedDocumentStore:
    """Write and read processed document JSON artifacts."""

    def __init__(self, settings: Settings) -> None:
        self._output_dir = settings.processed_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        processed: ProcessedDocument,
        chunks: list[Chunk],
        structured: StructuredFields | None = None,
    ) -> Path:
        document_id = processed.record.document_id
        output_path = self._output_dir / f"{document_id}.json"
        payload = ProcessedDocumentOutput(
            document=processed.record,
            chunks=chunks,
            full_text=processed.full_text,
            structured=structured or processed.structured,
        )

        try:
            json_text = json.dumps(
                _OUTPUT_ADAPTER.dump_python(payload),
                indent=2,
                ensure_ascii=False,
                default=str,
            )
            output_path.write_text(json_text, encoding="utf-8")
        except OSError as exc:
            logger.exception("Failed to write processed output: %s", output_path)
            raise DocumentProcessingError(f"Cannot write processed JSON: {output_path}") from exc

        logger.info("Saved processed output to %s", output_path)
        return output_path

    def load(self, document_id: str) -> ProcessedDocumentOutput:
        output_path = self._output_dir / f"{document_id}.json"
        if not output_path.exists():
            raise DocumentProcessingError(f"Processed document not found: {document_id}")
        try:
            data = json.loads(output_path.read_text(encoding="utf-8"))
            return _OUTPUT_ADAPTER.validate_python(data)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.exception("Failed to read processed output: %s", output_path)
            raise DocumentProcessingError(f"Cannot read processed JSON: {output_path}") from exc
