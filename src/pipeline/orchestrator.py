"""Pipeline orchestrator — coordinates stages via injected interfaces."""

from __future__ import annotations

import uuid
from pathlib import Path

from src.config import Settings, get_settings
from src.exceptions import DocumentProcessingError, LearningError, PipelineError, RetrievalError
from src.generation.draft_store import DraftStore
from src.learning.report import LearningReportGenerator
from src.learning.store import SqliteLearningStore
from src.logging_config import get_logger
from src.models.draft import DraftOutput
from src.models.document import ProcessedDocument
from src.models.learning import DraftRun, EditSession
from src.models.processing_output import ProcessedDocumentOutput
from src.pipeline.dependencies import PipelineDependencies
from src.pipeline.interfaces import PipelineRunner
from src.processing.storage import ProcessedDocumentStore

logger = get_logger(__name__)


class DocumentPipeline(PipelineRunner):
    """End-to-end orchestrator using injected stage interfaces."""

    def __init__(
        self,
        dependencies: PipelineDependencies,
        *,
        settings: Settings | None = None,
        learning_store: SqliteLearningStore | None = None,
    ) -> None:
        self._deps = dependencies
        self._settings = settings or get_settings()
        self._store = ProcessedDocumentStore(self._settings)
        self._draft_store = DraftStore(self._settings)
        self._learning_store = learning_store

    def process_documents(self, input_path: Path) -> list[ProcessedDocument]:
        input_path = input_path.resolve()
        logger.info("process_documents started", extra={"extra_fields": {"input": str(input_path)}})

        try:
            sources = self._deps.loader.discover(input_path)
        except DocumentProcessingError as exc:
            raise PipelineError(str(exc)) from exc

        if not sources:
            logger.warning("No supported documents found at %s", input_path)
            return []

        results: list[ProcessedDocument] = []
        errors: list[str] = []

        for source_path in sources:
            try:
                results.append(self._process_one(source_path))
            except DocumentProcessingError as exc:
                logger.error("Failed to process %s: %s", source_path, exc)
                errors.append(f"{source_path.name}: {exc}")

        if errors and not results:
            raise PipelineError("All documents failed processing:\n" + "\n".join(errors))
        if errors:
            logger.warning(
                "Completed with %s failure(s): %s",
                len(errors),
                "; ".join(errors),
            )

        logger.info("process_documents finished: %s document(s)", len(results))
        return results

    def _process_one(self, source_path: Path) -> ProcessedDocument:
        record = self._deps.loader.load(source_path)
        processed = self._deps.processor.process(record)
        structured = self._deps.structured_extractor.extract(processed)
        processed = processed.model_copy(update={"structured": structured})
        chunks = list(self._deps.chunker.chunk(processed))
        self._store.save(processed, chunks, structured=structured)
        document_id = processed.record.document_id
        try:
            self._deps.vector_index.index(document_id, chunks)
        except RetrievalError as exc:
            raise PipelineError(str(exc)) from exc
        return processed

    def generate_draft(
        self,
        doc_id: str,
        *,
        use_learning: bool = False,
        run_label: str | None = None,
    ) -> DraftOutput:
        logger.info(
            "generate_draft started",
            extra={
                "extra_fields": {
                    "doc_id": doc_id,
                    "use_learning": use_learning,
                    "run_label": run_label,
                }
            },
        )

        stored = self._load_processed(doc_id)
        processed = ProcessedDocument(
            record=stored.document,
            structured=stored.structured,
            full_text=stored.full_text,
        )

        evidence = list(self._deps.retriever.retrieve(doc_id))

        patterns = []
        preferences = []
        if use_learning and self._settings.learning_enabled:
            store = self._get_learning_store()
            patterns = list(store.get_relevant_patterns(doc_id))
            preferences = list(store.get_preferences())
            logger.info("Loaded %s learned pattern(s) for generation", len(patterns))

        draft = self._deps.draft_generator.generate(
            doc_id,
            processed,
            evidence,
            learned_patterns=patterns if use_learning else None,
            preferences=preferences if use_learning else None,
        )
        draft = self._deps.grounding_validator.validate(draft, evidence)
        self._draft_store.save(draft)

        if run_label and isinstance(self._get_learning_store(), SqliteLearningStore):
            self._get_learning_store().save_draft_run(
                DraftRun(
                    run_id=f"run_{uuid.uuid4().hex[:10]}",
                    draft_id=draft.draft_id,
                    doc_id=doc_id,
                    run_label=run_label,
                    used_learning=use_learning,
                    markdown=draft.markdown,
                )
            )

        return draft

    def learn_from_edit(
        self,
        draft_id: str,
        edited_markdown: str,
    ) -> EditSession:
        logger.info(
            "learn_from_edit started",
            extra={"extra_fields": {"draft_id": draft_id}},
        )
        try:
            draft = self._draft_store.load(draft_id)
        except Exception as exc:
            raise PipelineError(f"Cannot load draft '{draft_id}': {exc}") from exc

        try:
            session = self._deps.edit_capturer.capture(draft, edited_markdown)
            session = self._deps.pattern_extractor.extract(session)
            self._deps.learning_store.save_session(session)
        except LearningError as exc:
            raise PipelineError(str(exc)) from exc

        logger.info(
            "learn_from_edit finished: %s patterns saved",
            len(session.patterns),
        )
        return session

    def generate_learning_report(self, doc_id: str) -> Path:
        store = self._get_learning_store()
        if not isinstance(store, SqliteLearningStore):
            raise PipelineError("Learning report requires SqliteLearningStore.")
        generator = LearningReportGenerator(store, self._settings)
        return generator.generate(doc_id)

    def run_full(
        self,
        input_path: Path,
        doc_id: str,
        *,
        use_learning: bool = False,
        run_label: str | None = None,
    ) -> DraftOutput:
        logger.info(
            "run_full started",
            extra={
                "extra_fields": {
                    "input": str(input_path),
                    "doc_id": doc_id,
                    "use_learning": use_learning,
                }
            },
        )
        processed_list = self.process_documents(input_path)
        if not any(p.record.document_id == doc_id for p in processed_list):
            try:
                self._load_processed(doc_id)
            except DocumentProcessingError as exc:
                raise PipelineError(
                    f"Document '{doc_id}' was not processed from {input_path}."
                ) from exc
        return self.generate_draft(doc_id, use_learning=use_learning, run_label=run_label)

    def _load_processed(self, doc_id: str) -> ProcessedDocumentOutput:
        try:
            return self._store.load(doc_id)
        except DocumentProcessingError as exc:
            raise PipelineError(
                f"Document '{doc_id}' is not processed. Run `process` first."
            ) from exc

    def _get_learning_store(self) -> SqliteLearningStore:
        if self._learning_store is not None:
            return self._learning_store
        if isinstance(self._deps.learning_store, SqliteLearningStore):
            return self._deps.learning_store
        raise PipelineError("SqliteLearningStore is not configured.")
