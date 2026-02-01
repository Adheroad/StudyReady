# StudyReady - CBSE Question Paper Generator

AI-powered CBSE question paper generator with pixel-perfect formatting, bilingual support, and RAG-based intelligent question selection.

## 🎯 Features

- **📄 CBSE-Compliant PDF**: Exact recreation of official CBSE 2025 format (Commercial Art, XII)
- **🌐 Bilingual Support**: English + Hindi (Devanagari) in split layout
- **🤖 RAG-Powered Generation**: Vector search + LLM for contextually relevant questions
- **🔍 Automatic Extraction**: Scrapes CBSE website → Downloads PDFs → Extracts questions with Gemini Vision
- **⚡ Background Processing**: Async extraction to avoid timeouts
- **📊 Structured Output**: JSON-first LLM generation with strict schema validation
- **🎨 Pixel-Perfect Styling**: WeasyPrint templates with CBSE-accurate typography

## 🏗️ Architecture

```mermaid
graph LR
    A[CBSE Website] -->|Scrape| B[Downloader]
    B -->|PDF| C[Gemini Vision]
    C -->|Questions| D[PostgreSQL + pgvector]
    D -->|Vector Search| E[Question Selector]
    E -->|Context| F[LLM via OpenRouter]
    F -->|JSON| G[Jinja2 Template]
    G -->|HTML| H[WeasyPrint]
    H -->|PDF| I[User]
```

### Data Flow

1. **Ingestion**: `POST /admin/extract` → Scrape → Download → Extract → Embed → Store
2. **Generation**: `POST /papers/generate` → RAG Retrieval → LLM (JSON) → Template → PDF

## 🚀 Quick Start

See [`kickstart.md`](./kickstart.md) for full workflow. TL;DR:

```bash
# 1. Setup
cp Backend/.env.example Backend/.env  # Add API keys
docker compose up -d or make d-up

# 2. Ingest papers (background task, limit: 10)
curl -X POST "http://localhost:8000/api/v1/admin/extract?subject=commercial%20art&grade=XII&limit=10"

# 3. Generate paper
curl -X POST "http://localhost:8000/api/v1/papers/generate" \
  -H "Content-Type: application/json" \
  -d '{"subject": "Commercial Art", "grade": "XII", "total_marks": 36, "language": "both"}' \
  | jq -r '.paper_id' \
  | xargs -I {} curl "http://localhost:8000/api/v1/papers/{}/download?format=pdf" -o paper.pdf
```

## 📚 Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Python 3.11+ |
| **Database** | PostgreSQL 16 + pgvector |
| **LLM Gateway** | OpenRouter (GPT-4, Claude, Gemini) |
| **Vision** | google/gemini-2.0-flash-001 (OCR/extraction) |
| **Embeddings** | Gemini text-embedding-004 |
| **PDF Export** | WeasyPrint + Jinja2 |
| **DOCX Export** | python-docx |
| **Logging** | Loguru (structured + rotation) |
| **Container** | Docker + docker-compose |

## 🔌 API Reference

### Papers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/papers/generate` | Generate CBSE paper (returns paper_id) |
| `GET` | `/api/v1/papers/{id}` | Get paper metadata |
| `GET` | `/api/v1/papers/{id}/download?format=pdf` | Download PDF/DOCX |

### Questions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/questions/search?subject=...&query=...` | Semantic search |
| `GET` | `/api/v1/questions/stats` | Question count by subject |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/admin/extract?subject=...&limit=10` | Trigger background extraction |
| `GET` | `/api/v1/admin/papers` | List source papers |
| `GET` | `/api/v1/admin/status` | Extraction status |

## ⚙️ Configuration

Create `Backend/.env` from `.env.example`:

```bash
# API Keys
OPENROUTER_API_KEY=sk-or-...
GEMINI_API_KEY=AIzaSy...

# Database
DATABASE_URL=postgresql://studyready:password@localhost:5432/studyready

# Models (easily swappable)
GENERATION_MODEL=x-ai/grok-4.1-fast        # Paper formatting (will switch to better model)
VISION_MODEL=google/gemini-2.0-flash-001          # Question extraction
EMBEDDING_MODEL=openai/text-embedding-3-small  # Vector embeddings (will switch to larger model)

# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

## 📁 Project Structure

```
Backend/
├── app/
│   ├── api/              # FastAPI routes, schemas, dependencies
│   ├── core/             # Logging setup
│   ├── database/         # SQLAlchemy models (Paper, Question, GeneratedPaper)
│   ├── prompts/          # Externalized LLM prompts
│   │   ├── paper_formatting.md   # CBSE blueprint + JSON schema
│   │   └── question_extraction.md
│   ├── services/
│   │   ├── extraction/   # Gemini Vision, background tasks
│   │   ├── embeddings/   # Gemini embeddings
│   │   ├── generation/   # LLM paper generation
│   │   ├── retrieval/    # RAG (vector search, question selection)
│   │   ├── export/       # PDF (WeasyPrint), DOCX (python-docx)
│   │   └── papers/       # CBSE scraper, downloader
│   └── templates/
│       └── paper_pdf.html  # Jinja2 template (CBSE 2025 styling)
├── scripts/              # CLI utilities
│   ├── extract_papers.py   # Manual extraction
│   ├── ingest_papers.py    # Manual ingestion
│   └── cleanup_images.py   # Cleanup utility
├── tests/                # Pytest suite
├── alembic/              # Database migrations
├── docker-compose.yaml
└── Makefile
```

## 🎨 CBSE Paper Styling Highlights

- **Font**: Times New Roman (serif)
- **Layout**: Split (English full paper → page break → Hindi full paper)
- **Marks**: Section headers with calculation (e.g., "5 × 2 = 10")
- **Sub-points**: 
  - Bullets (`•`) for 2-mark questions
  - Roman numerals `(i), (ii), (iii)` for 6-mark questions
- **OR Questions**: Centered separator ("OR" / "अथवा")
- **Blueprint**: 8 MCQ (1 mark) + 5×2 marks (with OR) + 3×6 marks (sub-parts) = **36 marks**

## 🧪 Development

```bash
# Run tests
make test           # All tests
make test-unit      # Unit only

# Code quality
make lint           # Ruff + type checking
make format         # Auto-format

# Database
make d-up          # Start PostgreSQL
make d-migrate     # Run migrations
make d-res         # restart
```

## 📊 Implementation Status

- ✅ **Phase 0**: Logging infrastructure (Loguru)
- ✅ **Phase 1**: Project setup & configuration
- ✅ **Phase 2**: Data extraction pipeline (Gemini Vision)
- ✅ **Phase 3**: RAG system (pgvector + embeddings)
- ✅ **Phase 4**: Paper generation & export (LLM + PDF/DOCX)
- ✅ **Phase 6**: Visual refinement (pixel-perfect CBSE styling)

## 🤝 Why OpenRouter?

**OpenRouter** provides unified API access to multiple LLM providers:
- ✅ Single API key for GPT-4, Claude, Gemini, etc.
- ✅ Easy model switching via env var
- ✅ No infrastructure overhead
- ✅ Better quality than self-hosted open-source models for structured JSON generation

Alternative: HuggingFace would require GPU infrastructure or limited free-tier API.

## 📝 License

MIT

---

**Quick Links**: [`kickstart.md`](./kickstart.md) · [`RAG_GUIDE.md`](./RAG_GUIDE.md)
1 feb 2025