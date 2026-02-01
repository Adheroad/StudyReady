"""Question search and management API routes."""

from typing import Optional

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.api.schemas.question import QuestionResponse
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


from sqlalchemy import func, select
from app.database.models import Question, Paper
from app.services.retrieval.search import hybrid_search

@router.get("/search", response_model=list[QuestionResponse])
async def search_questions(
    db: SessionDep,
    query: Optional[str] = None,
    subject: Optional[str] = None,
    marks: Optional[int] = None,
    section: Optional[str] = None,
    limit: int = 20,
):
    """Search questions using metadata filters (RAG implementation in retrieval service)."""
    logger.info("Searching questions", query=query, subject=subject, marks=marks, limit=limit)
    
    questions = hybrid_search(
        db=db,
        query=query,
        subject=subject,
        marks=marks,
        section=section,
        limit=limit,
    )
    
    return questions


@router.get("/stats")
async def get_question_stats(db: SessionDep):
    """Get statistics about available questions."""
    total_q = db.execute(select(func.count(Question.id))).scalar()
    total_p = db.execute(select(func.count(Paper.id))).scalar()
    
    # Get subjects from associated papers
    subjects_stmt = select(Paper.subject).join(Question).distinct()
    subjects = db.execute(subjects_stmt).scalars().all()
    
    return {
        "total_questions": total_q or 0,
        "subjects": subjects,
        "papers_processed": total_p or 0,
    }
