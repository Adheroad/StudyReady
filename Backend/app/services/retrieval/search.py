"""Vector search service for question retrieval using pgvector."""

from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.database.models import Question, Paper
from app.services.embeddings.gemini_embeddings import generate_query_embedding
from app.core.logging import get_logger

logger = get_logger(__name__)


def vector_search(
    db: Session,
    query: str,
    limit: int = 20,
) -> list[Question]:
    """
    Perform pure vector similarity search.

    Args:
        db: Database session
        query: Search query text
        limit: Maximum results to return

    Returns:
        List of questions ordered by similarity
    """
    # Generate query embedding
    query_embedding = generate_query_embedding(query)

    # Use pgvector cosine distance for similarity search
    stmt = (
        select(Question)
        .filter(Question.embedding.isnot(None))
        .order_by(Question.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )

    results = db.execute(stmt).scalars().all()
    logger.info("Vector search completed", query=query[:50], results=len(results))
    return list(results)


def hybrid_search(
    db: Session,
    query: Optional[str] = None,
    subject: Optional[str] = None,
    grade: Optional[str] = None,
    year: Optional[str] = None,
    section: Optional[str] = None,
    question_type: Optional[str] = None,
    marks: Optional[int] = None,
    limit: int = 50,
) -> list[Question]:
    """
    Hybrid search combining vector similarity with metadata filtering.

    Args:
        db: Database session
        query: Optional semantic query for vector search
        subject: Filter by subject
        grade: Filter by grade (e.g., "10", "12")
        year: Filter by year (e.g., "2023", "2024")
        section: Filter by section (A, B, C, D, E)
        question_type: Filter by type (mcq, short, long, etc.)
        marks: Filter by marks value
        limit: Maximum results

    Returns:
        List of matching questions
    """
    # Build base query with paper join for subject filtering
    stmt = select(Question).join(Paper, Question.paper_id == Paper.id)

    # Apply metadata filters
    filters = []

    if subject:
        filters.append(Paper.subject.ilike(f"%{subject}%"))

    if grade:
        filters.append(Paper.grade == grade)

    if year:
        filters.append(Paper.year == year)

    if section:
        filters.append(Question.section == section)

    if question_type:
        filters.append(Question.question_type == question_type)

    if marks:
        filters.append(Question.marks == marks)

    if filters:
        stmt = stmt.filter(and_(*filters))

    # If query provided, order by vector similarity
    if query:
        query_embedding = generate_query_embedding(query)
        stmt = stmt.filter(Question.embedding.isnot(None))
        stmt = stmt.order_by(Question.embedding.cosine_distance(query_embedding))
    else:
        # Default ordering by creation date
        stmt = stmt.order_by(Question.created_at.desc())

    stmt = stmt.limit(limit)

    results = db.execute(stmt).scalars().all()
    logger.info(
        "Hybrid search completed",
        query=query[:30] if query else None,
        subject=subject,
        results=len(results),
    )
    return list(results)


def get_similar_questions(
    db: Session,
    question_id: str,
    limit: int = 10,
) -> list[Question]:
    """
    Find questions similar to a given question.

    Args:
        db: Database session
        question_id: UUID of the reference question
        limit: Maximum similar questions to return

    Returns:
        List of similar questions (excluding the reference)
    """
    # Get the reference question
    ref_question = db.get(Question, question_id)
    if not ref_question or ref_question.embedding is None:
        logger.warning("Reference question not found or has no embedding", id=question_id)
        return []

    # Find similar by embedding
    stmt = (
        select(Question)
        .filter(Question.id != question_id)
        .filter(Question.embedding.isnot(None))
        .order_by(Question.embedding.cosine_distance(ref_question.embedding))
        .limit(limit)
    )

    results = db.execute(stmt).scalars().all()
    return list(results)
