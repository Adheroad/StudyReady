"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, papers, questions
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
    if settings.DEBUG:
        Base.metadata.create_all(bind=engine)
        logger.debug("Database tables created")

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title="CBSE Question Paper Generator",
    description="Generate CBSE-format question papers from extracted questions",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
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
app.include_router(papers.router, prefix="/api/v1/papers", tags=["Papers"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


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
