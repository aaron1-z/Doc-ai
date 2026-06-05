"""Command-line entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from src.config import get_settings
from src.exceptions import AmbitioError, PipelineError
from src.logging_config import setup_logging

app = typer.Typer(
    name="ambitio-doc",
    help="Ambitio document AI — processing, grounded drafts, and edit learning.",
    no_args_is_help=True,
)
console = Console()


def _bootstrap() -> None:
    settings = get_settings()
    setup_logging(settings)
    settings.ensure_directories()


@app.callback()
def main(ctx: typer.Context) -> None:
    """Initialize logging and configuration from `.env` in the project root."""
    _bootstrap()
    ctx.ensure_object(dict)


@app.command("process")
def process(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Directory or file path containing source documents.",
        exists=True,
        file_okay=True,
        dir_okay=True,
    ),
) -> None:
    """Ingest and process source documents."""
    from src.pipeline.factory import create_pipeline

    try:
        pipeline = create_pipeline()
        results = pipeline.process_documents(input)
        console.print(f"[green]Processed {len(results)} document(s).[/green]")
    except (PipelineError, AmbitioError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("draft")
def draft(
    doc_id: str = typer.Option(..., "--doc-id", "-d", help="Document identifier."),
    use_learning: bool = typer.Option(
        False,
        "--use-learning",
        help="Apply learned operator preferences from past edits.",
    ),
    run_label: Optional[str] = typer.Option(
        None,
        "--run-label",
        help="Label this generation run (e.g. run1, run2) for learning reports.",
    ),
) -> None:
    """Generate a grounded draft for a processed document."""
    from src.pipeline.factory import create_pipeline

    try:
        pipeline = create_pipeline()
        output = pipeline.generate_draft(
            doc_id,
            use_learning=use_learning,
            run_label=run_label,
        )
        console.print(f"[green]Draft generated:[/green] {output.draft_id}")
        if run_label:
            console.print(f"[dim]Run label:[/dim] {run_label}")
    except (PipelineError, AmbitioError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("learn")
def learn(
    draft_id: str = typer.Option(..., "--draft-id", help="Draft identifier."),
    edited_file: Optional[Path] = typer.Option(
        None,
        "--edited-file",
        "-e",
        help="Path to operator-edited markdown (stdin if omitted).",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
) -> None:
    """Capture operator edits and extract learning signals."""
    from src.pipeline.factory import create_pipeline

    try:
        if edited_file is not None:
            edited_markdown = edited_file.read_text(encoding="utf-8")
        else:
            console.print("[yellow]Provide --edited-file (interactive stdin not yet supported).[/yellow]")
            raise typer.Exit(code=1)

        pipeline = create_pipeline()
        session = pipeline.learn_from_edit(draft_id, edited_markdown)
        console.print(f"[green]Edit session saved:[/green] {session.session_id}")
    except (PipelineError, AmbitioError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("run")
def run(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Directory or file path containing source documents.",
        exists=True,
        file_okay=True,
        dir_okay=True,
    ),
    doc_id: str = typer.Option(..., "--doc-id", "-d", help="Document identifier."),
    use_learning: bool = typer.Option(
        False,
        "--use-learning",
        help="Apply learned operator preferences.",
    ),
) -> None:
    """Run full pipeline: process → draft."""
    from src.pipeline.factory import create_pipeline

    try:
        pipeline = create_pipeline()
        output = pipeline.run_full(input, doc_id, use_learning=use_learning)
        console.print(f"[green]Pipeline complete. Draft:[/green] {output.draft_id}")
    except (PipelineError, AmbitioError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("index")
def index(
    doc_id: str = typer.Option(..., "--doc-id", "-d", help="Document identifier."),
) -> None:
    """Re-index chunks for a processed document from saved JSON."""
    from src.exceptions import DocumentProcessingError, RetrievalError
    from src.processing.storage import ProcessedDocumentStore
    from src.retrieval import create_retrieval_service

    try:
        settings = get_settings()
        stored = ProcessedDocumentStore(settings).load(doc_id)
        retrieval = create_retrieval_service(settings)
        retrieval.index_document(doc_id, stored.chunks)
        console.print(f"[green]Indexed {len(stored.chunks)} chunk(s) for {doc_id}.[/green]")
    except (DocumentProcessingError, RetrievalError, AmbitioError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("search")
def search(
    query: str = typer.Option(..., "--query", "-q", help="Search query."),
    doc_id: Optional[str] = typer.Option(
        None,
        "--doc-id",
        "-d",
        help="Limit search to a single document.",
    ),
    top_k: Optional[int] = typer.Option(
        None,
        "--top-k",
        "-k",
        help="Number of results (default from RETRIEVAL_TOP_K).",
    ),
) -> None:
    """Semantic search over indexed document chunks."""
    from src.exceptions import RetrievalError
    from src.retrieval import create_retrieval_service

    try:
        retrieval = create_retrieval_service(get_settings())
        results = retrieval.semantic_search(query, document_id=doc_id, top_k=top_k)
        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return
        for hit in results:
            console.print(
                f"[bold]{hit.chunk_id}[/bold] (page {hit.page}, score {hit.score:.3f})\n{hit.text[:200]}..."
            )
    except (RetrievalError, AmbitioError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("learning-report")
def learning_report(
    doc_id: str = typer.Option(..., "--doc-id", "-d", help="Document identifier."),
) -> None:
    """Generate Run 1 vs Run 2 learning improvement report."""
    from src.pipeline.factory import create_pipeline

    try:
        pipeline = create_pipeline()
        path = pipeline.generate_learning_report(doc_id)
        console.print(f"[green]Learning report written to:[/green] {path}")
    except (PipelineError, AmbitioError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("info")
def info() -> None:
    """Print resolved configuration (secrets redacted)."""
    settings = get_settings()
    console.print("[bold]Ambitio Doc AI[/bold]")
    console.print(f"  Environment: {settings.app_env.value}")
    console.print(f"  Log level:   {settings.log_level}")
    console.print(f"  Data dir:    {settings.data_dir}")
    console.print(f"  Config file: .env (project root)")
    console.print(f"  Gemini key:  {'set' if settings.gemini_api_key else 'not set'}")


if __name__ == "__main__":
    app()
