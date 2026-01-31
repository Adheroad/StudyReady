"""Admin API routes for paper extraction and management."""

from fastapi import APIRouter, BackgroundTasks

from app.api.deps import SessionDep, SettingsDep
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/extract")
async def trigger_extraction(
    subject: str,
    db: SessionDep,
    settings: SettingsDep,
    background_tasks: BackgroundTasks,
    grade: str = None,
    year: str = None,
    limit: int = None,
):
    """
    Trigger paper extraction for a subject.

    Runs in background to avoid timeout.
    """
    logger.info(
        "Extraction triggered",
        subject=subject,
        grade=grade,
        year=year,
        limit=limit,
    )

    # TODO: Add background task for extraction
    # background_tasks.add_task(extract_papers, subject, grade, year, limit)

    return {
        "status": "queued",
        "message": f"Extraction queued for subject: {subject}",
        "params": {"subject": subject, "grade": grade, "year": year, "limit": limit},
    }


@router.get("/papers")
async def list_source_papers(db: SessionDep):
    """List all source papers in database."""
    from app.database.models import Paper
    from sqlalchemy import select

    stmt = select(Paper).order_by(Paper.created_at.desc())
    papers = db.execute(stmt).scalars().all()

    return [
        {
            "id": str(p.id),
            "subject": p.subject,
            "grade": p.grade,
            "year": p.year,
            "processed": p.processed,
        }
        for p in papers
    ]


@router.get("/status")
async def get_extraction_status():
    """Get current extraction status."""
    return {"status": "idle", "current_task": None}
