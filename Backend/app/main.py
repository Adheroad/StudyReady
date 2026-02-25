"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, ncert, papers, questions, external_cbse
from app.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database.connection import Base, engine

# Initialize settings and logging
settings = get_settings()
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    debug=settings.DEBUG,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(
        "Starting application",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
    )

    # Create tables (for development - use Alembic in production)
    Base.metadata.create_all(bind=engine)
    logger.debug("Database tables created")
    
    # Apply database schema patches if needed
    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE generated_papers ADD COLUMN IF NOT EXISTS pattern_hash VARCHAR(64);"))
            conn.execute(text("ALTER TABLE generated_papers ADD COLUMN IF NOT EXISTS validation_result JSONB;"))
            conn.execute(text("ALTER TABLE generated_papers ADD COLUMN IF NOT EXISTS question_count INTEGER;"))
        logger.info("Database schema patched successfully.")
    except Exception as e:
        logger.warning(f"Could not patch database schema: {e}")

    # Create admin user on startup
    from app.database.connection import get_db
    from app.services.auth import create_admin_user
    db = next(get_db())
    try:
        admin_user = create_admin_user(db)
        if admin_user:
            logger.info(f"Admin user ready: {admin_user.email}")
    except Exception as e:
        logger.warning(f"Could not create admin user: {e}")
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title="StudyReady - CBSE Question Paper Generator API",
    description="""
## AI-Powered CBSE Question Paper Generation

Generate pixel-perfect, CBSE-compliant question papers with bilingual support (English + Hindi).

### Key Features
- 📄 **RAG-Powered Generation**: Intelligent question selection using vector embeddings
- 🌐 **Bilingual Support**: English and Hindi (Devanagari) in official CBSE format
- 🎨 **Pixel-Perfect Styling**: Exact recreation of CBSE 2025 paper format
- 🤖 **LLM Integration**: GPT-4, Claude, Gemini via OpenRouter
- 📥 **Auto-Extraction**: Scrapes CBSE website and extracts questions with Gemini Vision

### Workflow
1. **Ingest**: `POST /admin/extract` → Scrape CBSE → Download PDFs → Extract + Embed → Store
2. **Generate**: `POST /papers/generate` → RAG Retrieval → LLM (JSON) → PDF Export

### Quick Start
```bash
# 1. Ingest papers
curl -X POST "http://localhost:8000/api/v1/admin/extract?subject=commercial%20art&limit=10"

# 2. Generate paper
curl -X POST "http://localhost:8000/api/v1/papers/generate" \\
  -H "Content-Type: application/json" \\
  -d '{"subject":"Commercial Art","grade":"XII","total_marks":36,"language":"both"}'
```

For complete workflow, see: [kickstart.md](https://github.com/yourusername/StudyReady/blob/main/kickstart.md)
    """,
    version="1.0.1",
    contact={
        "name": "StudyReady Team",
        "url": "https://github.com/yourusername/StudyReady",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_tags=[
        {
            "name": "Papers",
            "description": "Generate and download CBSE question papers in PDF/DOCX format",
        },
        {
            "name": "Questions",
            "description": "Search and retrieve questions from the database using semantic search",
        },
        {
            "name": "Admin",
            "description": "Background paper extraction from CBSE website (scraping + OCR + embedding)",
        },
        {
            "name": "External CBSE",
            "description": "Browse and interact with the CBSE website directly (Legacy)",
        },
        {
            "name": "NCERT",
            "description": "Browse and ingest NCERT textbooks (Class X and XII)",
        },
    ],
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(papers.router, prefix="/api/v1/papers", tags=["Papers"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(external_cbse.router, prefix="/api/v1/external", tags=["External CBSE"])
app.include_router(ncert.router, prefix="/api/v1/ncert", tags=["NCERT"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "CBSE Question Paper Generator API",
        "version": "1.0.0",
        "docs": "/docs",
    }
