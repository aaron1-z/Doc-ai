"""Document processing unit tests."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from src.config import Settings, reset_settings_cache
from src.models.document import DocumentRecord, ExtractedPage
from src.processing.aggregator import (
    aggregate_confidence,
    aggregate_extraction_method,
    build_full_text,
)
from src.processing.chunker import SlidingWindowChunker
from src.processing.constants import EXTRACTION_NATIVE
from src.processing.loader import FileDocumentLoader, make_document_id
from src.processing.storage import ProcessedDocumentStore


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "sample_deed.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Grantor: John Smith. Grantee: Jane Doe. Parcel ID: 123-456.")
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    reset_settings_cache()
    return Settings(
        processed_dir=tmp_path / "processed",
        chunk_size=500,
        chunk_overlap=100,
        native_text_min_chars=10,
    )


def test_make_document_id_is_stable(sample_pdf: Path) -> None:
    assert make_document_id(sample_pdf) == make_document_id(sample_pdf)


def test_loader_discovers_pdf(sample_pdf: Path) -> None:
    loader = FileDocumentLoader()
    files = loader.discover(sample_pdf.parent)
    assert sample_pdf in files


def test_loader_builds_record(sample_pdf: Path) -> None:
    record = FileDocumentLoader().load(sample_pdf)
    assert record.document_id
    assert record.source_path == sample_pdf.resolve()
    assert record.pages == []


def test_aggregate_native_method() -> None:
    pages = [
        ExtractedPage(
            page_number=1,
            text="hello",
            extraction_method=EXTRACTION_NATIVE,
            confidence=0.9,
        )
    ]
    assert aggregate_extraction_method(pages) == EXTRACTION_NATIVE
    assert aggregate_confidence(pages) == pytest.approx(0.9)


def test_sliding_window_chunker(settings: Settings, sample_pdf: Path) -> None:
    from src.processing.processor import DefaultDocumentProcessor

    record = FileDocumentLoader().load(sample_pdf)
    processed = DefaultDocumentProcessor(settings).process(record)
    chunks = SlidingWindowChunker(settings).chunk(processed)
    assert len(chunks) >= 1
    assert all(c.metadata.doc_id == record.document_id for c in chunks)


def test_save_processed_json(settings: Settings, sample_pdf: Path) -> None:
    from src.processing.processor import DefaultDocumentProcessor

    record = FileDocumentLoader().load(sample_pdf)
    processed = DefaultDocumentProcessor(settings).process(record)
    chunks = list(SlidingWindowChunker(settings).chunk(processed))
    store = ProcessedDocumentStore(settings)
    path = store.save(processed, chunks)
    assert path.exists()
    loaded = store.load(record.document_id)
    assert loaded.document.document_id == record.document_id
    assert len(loaded.chunks) == len(chunks)
    assert "Grantor" in loaded.full_text


def test_build_full_text_includes_pages() -> None:
    pages = [
        ExtractedPage(
            page_number=1,
            text="Line one",
            extraction_method=EXTRACTION_NATIVE,
            confidence=1.0,
        ),
        ExtractedPage(
            page_number=2,
            text="Line two",
            extraction_method=EXTRACTION_NATIVE,
            confidence=1.0,
        ),
    ]
    text = build_full_text(pages)
    assert "--- Page 1 ---" in text
    assert "--- Page 2 ---" in text
