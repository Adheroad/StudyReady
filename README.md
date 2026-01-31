# CBSE Question Paper Generator

A production-grade FastAPI application that generates CBSE-format question papers using AI-powered extraction and RAG (Retrieval-Augmented Generation).

## Features

- 📄 **PDF Extraction**: Uses Gemini Vision API to extract questions from CBSE papers
- 🔍 **Semantic Search**: Vector embeddings with pgvector for intelligent question retrieval
- 🤖 **AI Generation**: OpenRouter integration for GPT-4o/Claude/Gemini paper formatting
- 📊 **Production Logging**: Loguru-based structured logging with rotation
- 🧪 **Testing**: Comprehensive unit, integration, and e2e test suites

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Database | PostgreSQL + pgvector |
| Extraction | Gemini Vision API |
| Embeddings | Gemini Embedding API |
| Generation | OpenRouter (GPT-4o, Claude, etc.) |
| Export | WeasyPrint (PDF), python-docx (DOCX) |
| Logging | Loguru |
| Testing | Pytest |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- API Keys: [OpenRouter](https://openrouter.ai/keys) + [Gemini](https://aistudio.google.com/app/apikey)

### Setup

```bash
# 1. Clone and navigate
cd Backend

# 2. Copy environment file
cp .env.example .env
# Edit .env with your API keys

# 3. Start database
docker compose up -d

# 4. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 5. Install dependencies
pip install -r requirements.txt

# 6. Test API keys
python scripts/test_keys.py

# 7. Run development server
make run
# or: uvicorn app.main:app --reload
```

### Extract Papers

```bash
# Extract Commercial Art papers (limit to 2 for testing)
python scripts/extract_papers.py --subject "commercial art" --limit 2

# Extract with grade filter
python scripts/extract_papers.py --subject "fine arts" --grade XII

# Skip embeddings for faster testing
python scripts/extract_papers.py --subject design --limit 1 --skip-embeddings
```

### RAG Ingestion Pipeline (Phase 3)

Store papers in the database with embeddings for semantic search:

```bash
# Ingest papers from CBSE website
python scripts/ingest_papers.py --subject "mathematics" --grade 12 --limit 5

# Ingest with year filter
python scripts/ingest_papers.py --subject "physics" --year 2024 --limit 3

# Ingest a local PDF file
python scripts/ingest_papers.py --pdf /path/to/paper.pdf --subject "chemistry" --grade 12 --year 2024
```

### Search Questions

```bash
# Start the server
make run

# Search via API
curl -X GET "http://localhost:8000/api/v1/questions/search?subject=mathematics&query=calculus"
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/papers/generate` | Generate question paper |
| `GET` | `/api/v1/questions/search` | Semantic + metadata search |
| `POST` | `/api/v1/admin/extract` | Trigger extraction |
| `GET` | `/api/v1/admin/papers` | List source papers |

## Project Structure

```
Backend/
├── app/
│   ├── api/          # Routes and schemas
│   ├── core/         # Logging, prompts
│   ├── prompts/      # External prompt templates
│   ├── database/     # Models, connection
│   └── services/     # Business logic
│       ├── papers/       # CBSE scraper, downloader
│       ├── extraction/   # Gemini Vision
│       ├── embeddings/   # OpenRouter embeddings
│       ├── retrieval/    # Vector search, selector
│       ├── generation/   # OpenRouter (Phase 4)
│       └── export/       # PDF/DOCX (Phase 4)
├── scripts/          # CLI tools
│   ├── test_keys.py      # API key validation
│   ├── extract_papers.py # Legacy extraction
│   └── ingest_papers.py  # RAG ingestion pipeline
├── tests/            # Unit, integration, e2e
├── docker-compose.yml
└── Makefile
```

## Development

```bash
# Run tests
make test           # All tests
make test-unit      # Unit tests only

# Code quality
make lint           # Ruff + mypy
make format         # Auto-format

# Database
make db-up          # Start DB
make db-down        # Stop DB
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM + embeddings |
| `DATABASE_URL` | PostgreSQL connection string |
| `VISION_MODEL` | Vision model (default: `google/gemini-2.0-flash-001`) |
| `EMBEDDING_MODEL` | Embedding model (default: `openai/text-embedding-3-small`) |
| `DEBUG` | Enable debug mode |

## Implementation Status

- [x] Phase 0: Logging infrastructure
- [x] Phase 1: Project setup & configuration
- [x] Phase 2: Data extraction pipeline
- [x] Phase 3: RAG system (vector search, ingestion)
- [ ] Phase 4: Paper generation & export

## License

MIT