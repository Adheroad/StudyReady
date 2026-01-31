"""Question search and management API routes."""

from typing import Optional

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.api.schemas.question import QuestionResponse
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/search", response_model=list[QuestionResponse])
async def search_questions(
    db: SessionDep,
    query: Optional[str] = None,
    subject: Optional[str] = None,
    marks: Optional[int] = None,
    section: Optional[str] = None,
    limit: int = 20,
):
    """
    Search questions using hybrid search.

    - Uses vector similarity for semantic search
    - Combines with SQL filters for metadata
    """
    logger.info(
        "Searching questions",
        query=query,
        subject=subject,
        marks=marks,
        limit=limit,
    )

    # TODO: Implement hybrid search in Phase 3
    return []


@router.get("/stats")
async def get_question_stats(db: SessionDep):
    """Get statistics about available questions."""
    # TODO: Implement stats
    return {
        "total_questions": 0,
        "subjects": [],
        "papers_processed": 0,
    }
