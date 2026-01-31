"""Paper generation API routes."""

from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep, SettingsDep
from app.api.schemas.paper import PaperGenerateRequest, PaperResponse
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate", response_model=PaperResponse)
async def generate_paper(
    request: PaperGenerateRequest,
    db: SessionDep,
    settings: SettingsDep,
):
    """
    Generate a question paper.

    - Retrieves questions from database using hybrid search
    - Selects questions based on marks distribution
    - Formats into CBSE paper format using LLM
    - Returns paper content and metadata
    """
    logger.info(
        "Generating paper",
        subject=request.subject,
        grade=request.grade,
        total_marks=request.total_marks,
    )

    # TODO: Implement in Phase 3-4
    # 1. Search questions
    # 2. Select questions
    # 3. Generate formatted paper
    # 4. Export PDF/DOCX

    raise HTTPException(
        status_code=501,
        detail="Paper generation not yet implemented. Complete Phase 3-4.",
    )


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: str, db: SessionDep):
    """Get a generated paper by ID."""
    # TODO: Implement retrieval
    raise HTTPException(status_code=404, detail="Paper not found")


@router.get("/{paper_id}/download")
async def download_paper(paper_id: str, format: str = "pdf"):
    """Download generated paper as PDF or DOCX."""
    # TODO: Implement download
    raise HTTPException(status_code=404, detail="Paper not found")
