# Doc AI

Document understanding, grounded drafting, and improvement from operator edits.

## Architecture Overview

 Doc AI is a modular document processing system built on a **dependency injection architecture** with clear separation of concerns. The system follows an interface-driven design pattern where each major component defines abstract contracts, enabling easy testing, extensibility, and implementation swapping.

### Core Architectural Principles

**Interface-Based Design**
- Every major subsystem (processing, retrieval, generation, learning) defines abstract interfaces in `interfaces.py` files
- Concrete implementations are injected via `PipelineDependencies` factory
- The orchestrator (`DocumentPipeline`) depends only on interfaces, not concrete classes
- This enables mocking for tests and swapping implementations (e.g., different vector stores)

**Layered Architecture**
```
CLI Layer (cli.py)
    ↓
Pipeline Layer (pipeline/orchestrator.py)
    ↓
Domain Interfaces (*/interfaces.py)
    ↓
Concrete Implementations (*/impl.py)
    ↓
Infrastructure (storage, databases, external APIs)
```

**Configuration Management**
- Centralized configuration via `config.py` using Pydantic Settings
- Environment variables and `.env` file are the single source of truth
- Settings are cached via `@lru_cache` for performance
- Type-safe with validation at startup

**Data Flow**
1. **Processing**: Raw documents → Extracted text → Structured fields → Chunks
2. **Retrieval**: Chunks → Embeddings → Vector index → Evidence bundles
3. **Generation**: Evidence + Learned patterns → Grounded draft
4. **Learning**: Draft + Operator edits → Diff → Pattern extraction → SQLite storage

### Module Architecture

**Processing Module** (`src/processing/`)
- `DocumentLoader`: Discovers and loads supported file types (PDF, images)
- `DocumentProcessor`: Extracts text via native PDF parsing or OCR fallback
- `StructuredFieldExtractor`: Derives metadata from processed text
- `TextChunker`: Splits documents into overlapping chunks for retrieval
- Storage: JSON files under `data/processed/`

**Retrieval Module** (`src/retrieval/`)
- `VectorIndex`: Abstract interface for chunk storage and search
- `ChromaStore`: ChromaDB implementation with persistence
- `Embeddings`: Sentence-transformers wrapper
- `Retriever`: Orchestrates search and evidence bundling
- `EvidenceBundler`: Applies abstention rules and scoring

**Generation Module** (`src/generation/`)
- `DraftGenerator`: LLM-powered draft creation with grounding
- `GroundingValidator`: Verifies claims against evidence
- `DraftStore`: Persists drafts to `data/drafts/`
- Prompts are versioned and support learned pattern injection

**Learning Module** (`src/learning/`)
- `EditCapturer`: Records original vs edited drafts with diffs
- `PatternExtractor`: Uses Gemini to extract reusable patterns
- `LearningStore`: SQLite persistence for patterns and preferences
- `LearningReportGenerator`: Creates human-readable reports

**Pipeline Module** (`src/pipeline/`)
- `DocumentPipeline`: Main orchestrator coordinating all stages
- `PipelineDependencies`: Factory for injecting implementations
- `PipelineRunner`: Abstract interface for end-to-end workflows

### Key Design Patterns

**Dependency Injection**
- `PipelineDependencies` aggregates all interface implementations
- Constructor injection throughout the codebase
- Enables test doubles and alternative implementations

**Repository Pattern**
- `ProcessedDocumentStore`, `DraftStore`, `LearningStore` abstract persistence
- Clear separation between business logic and data access
- Easy to swap storage backends

**Strategy Pattern**
- Multiple chunking strategies, embedding models, retrieval methods
- Configured via settings, selected at runtime

**Observer Pattern**
- Structured logging via `logging_config.py` with contextual fields
- Progress tracking through pipeline stages

### Technology Stack

**Core**
- Python 3.11+ with type hints throughout
- Pydantic for data validation and settings
- Typer for CLI with rich output

**Document Processing**
- PyMuPDF for native PDF text extraction
- Tesseract OCR for image and low-text PDF fallback
- pdf2image for PDF-to-image conversion

**Retrieval**
- sentence-transformers for embeddings
- ChromaDB for vector storage
- rank-bm25 for hybrid search

**Generation & Learning**
- Google Gemini API for pattern extraction and drafting
- SQLAlchemy with SQLite for learning persistence

**Development**
- pytest for testing
- ruff for linting
- mypy for type checking

## Requirements

- Python 3.11
- Tesseract OCR (optional until processing is implemented)
- Poppler (for `pdf2image`, optional until processing is implemented)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Create `.env` in the project root (see variables below). **Only `.env` is used for configuration** — set `GEMINI_API_KEY` there.

## CLI

```bash
python -m src --help
python -m src process --input ./data/samples
python -m src draft --doc-id example_001
python -m src learn --draft-id example_001
python -m src run --input ./data/samples --doc-id example_001
```

Or after editable install:

```bash
pip install -e .
ambitio-doc --help
```

## Project Layout

```
src/
  config.py           # Settings from environment / .env
  logging_config.py   # Structured logging setup
  cli.py              # Typer entrypoint
  models/             # Domain types (Pydantic)
  processing/         # Document extraction interfaces
  retrieval/          # Grounded retrieval interfaces
  generation/         # Draft generation interfaces
  learning/           # Operator-edit learning interfaces
  pipeline/           # Orchestration (depends on interfaces only)
```

### Document Processing (Implemented)

- PDF: PyMuPDF native text per page; OCR fallback when text length < `NATIVE_TEXT_MIN_CHARS`
- Images: PNG, JPG, TIFF, WebP, BMP via Tesseract OCR
- Chunking: 500 chars with 100 overlap (configurable)
- Output: `data/processed/{document_id}.json`

```bash
python -m src process --input ./data/samples
```

Requires [Tesseract](https://github.com/tesseract-ocr/tesseract) on PATH (or set `TESSERACT_CMD` in `.env`) for OCR paths.

### Retrieval (Implemented)

- Embeddings: `sentence-transformers` (`all-MiniLM-L6-v2`, configurable)
- Vector store: ChromaDB persisted under `CHROMA_PERSIST_DIR` (default `./data/chroma`)
- Auto-indexes chunks after `process`; re-index with `index` command
- `RETRIEVAL_TOP_K` controls default search result count

```bash
python -m src process --input ./data/samples
python -m src index --doc-id <document_id>
python -m src search --query "grantor name" --doc-id <document_id> --top-k 5
```

### Learning from Operator Edits (Implemented)

- Saves `original.md`, `edited.md`, and `diff.patch` under `data/edits/{session_id}/`
- Compares versions with unified diff
- Extracts reusable patterns via **Gemini** (terminology, section emphasis, required fields)
- Stores patterns in **SQLite** (`data/ambitio.db`)
- Injects learned rules into Run 2+ draft prompts with `--use-learning`

```bash
# Set GEMINI_API_KEY in .env first
python -m src draft --doc-id <id> --run-label run1
python scripts/simulate_operator_edits.py data/drafts/<draft>.md data/edits/edited.md
python -m src learn --draft-id <draft_id> --edited-file data/edits/edited.md
python -m src draft --doc-id <id> --run-label run2 --use-learning
python -m src learning-report --doc-id <id>

# Or run the full demo:
python scripts/demo_learning.py --doc-id <id>
```

Report written to `docs/learning_report.md` (configurable via `LEARNING_REPORT_PATH`).

## Configuration

All configuration is managed through environment variables in `.env`:

```bash
# Application
APP_ENV=development
LOG_LEVEL=INFO
LOG_FORMAT=text

# Paths
DATA_DIR=./data
PROCESSED_DIR=./data/processed
DRAFTS_DIR=./data/drafts
EDITS_DIR=./data/edits
DATABASE_URL=sqlite:///./data/ambitio.db

# Document Processing
TESSERACT_CMD=tesseract
OCR_LANGUAGE=eng
OCR_CONFIDENCE_THRESHOLD=0.5
NATIVE_TEXT_MIN_CHARS=50
CHUNK_SIZE=500
CHUNK_OVERLAP=100

# Retrieval
EMBEDDING_MODEL=all-MiniLM-L6-v2
RETRIEVAL_TOP_K=8
RETRIEVAL_MIN_SCORE=0.35
CHROMA_PERSIST_DIR=./data/chroma

# Gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_MAX_TOKENS=4096
GEMINI_TEMPERATURE=0.2

# Learning
LEARNING_ENABLED=true
LEARNING_SIMILAR_EDITS_K=3
LEARNING_REPORT_PATH=./docs/learning_report.md
```

## Development

```bash
pip install pytest ruff
pytest
ruff check src/
mypy src/
```

## Testing Strategy

The architecture supports comprehensive testing through:
- Interface-based design enables easy mocking
- Dependency injection allows test doubles
- Pydantic models simplify test data construction
- SQLite in-memory for learning store tests
- ChromaDB ephemeral mode for retrieval tests


## Results


<img width="1548" height="355" alt="WhatsApp Image 2026-06-05 at 10 36 32" src="https://github.com/user-attachments/assets/f6c47be0-e2a5-4cca-8251-0ce86bcff3b7" />



<img width="1537" height="751" alt="WhatsApp Image 2026-06-05 at 10 37 54" src="https://github.com/user-attachments/assets/1b3e9ec4-3df4-4b35-a8b3-602ca65fbd6b" />


<img width="1554" height="944" alt="WhatsApp Image 2026-06-05 at 10 38 25" src="https://github.com/user-attachments/assets/9d29731d-b653-4ec6-a188-2c20f6d19c5b" />


<img width="1576" height="520" alt="WhatsApp Image 2026-06-05 at 10 39 36" src="https://github.com/user-attachments/assets/83dcf394-cc43-40a7-bd75-447ce17507a6" />


<img width="1551" height="166" alt="WhatsApp Image 2026-06-05 at 10 40 08" src="https://github.com/user-attachments/assets/0b114c4a-df59-4bd4-8e77-40bd28373968" />




