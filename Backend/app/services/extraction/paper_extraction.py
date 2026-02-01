"""Background task wrapper for paper extraction."""

from app.config import get_settings
from app.core.logging import get_logger
from app.database.connection import SessionLocal
from app.database.models import Paper, Question
from app.services.embeddings.gemini_embeddings import generate_embedding
from app.services.extraction.gemini_vision import extract_questions_from_pdf
from app.services.papers.cbse_scraper import get_papers_by_subject
from app.services.papers.downloader import download_paper

logger = get_logger(__name__)


def extract_papers_background(
    subject: str,
    grade: str = None,
    year: str = None,
    limit: int = None,
    skip_embeddings: bool = False,
):
    """
    Background task for extracting papers.
    
    Args:
        subject: Subject name filter
        grade: Optional grade filter (e.g., "XII")
        year: Optional year filter (e.g., "2024")
        limit: Optional max papers to process (default: 10)
        skip_embeddings: Skip embedding generation for faster processing
    """
    logger.info(
        "Background extraction started",
        subject=subject,
        grade=grade,
        year=year,
        limit=limit,
    )

    db = SessionLocal()
    processed_count = 0
    error_count = 0

    try:
        # Fetch papers from CBSE website
        papers = get_papers_by_subject(subject, grade, year)

        if not papers:
            logger.warning("No papers found", subject=subject)
            return {"status": "completed", "processed": 0, "errors": 0}

        # Apply limit (default to 10 to avoid long processing)
        if limit:
            papers = papers[:limit]
        else:
            papers = papers[:10]  # Default limit

        logger.info("Papers to process", count=len(papers))

        for idx, paper_info in enumerate(papers, 1):
            logger.info(
                "Processing paper",
                index=f"{idx}/{len(papers)}",
                subject=paper_info["subject"],
                year=paper_info.get("year", "unknown"),
            )

            try:
                _process_single_paper(db, paper_info, skip_embeddings)
                processed_count += 1
            except Exception as e:
                logger.error(
                    "Failed to process paper",
                    subject=paper_info["subject"],
                    year=paper_info.get("year"),
                    error=str(e),
                )
                error_count += 1
                continue

        logger.info(
            "Extraction complete",
            processed=processed_count,
            errors=error_count,
        )

        return {
            "status": "completed",
            "processed": processed_count,
            "errors": error_count,
        }

    except Exception as e:
        logger.error("Extraction failed", error=str(e))
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


def _process_single_paper(db, paper_info: dict, skip_embeddings: bool = False):
    """Process a single paper: download, extract, store."""
    # Download
    pdf_path = download_paper(paper_info)
    logger.debug("Downloaded paper", path=pdf_path)

    # Check if already processed (case-insensitive subject match)
    from sqlalchemy import func
    
    existing = (
        db.query(Paper)
        .filter(
            func.lower(Paper.subject) == paper_info["subject"].lower(),
            Paper.year == paper_info.get("year", ""),
            Paper.grade == paper_info.get("grade", "XII"),
        )
        .first()
    )

    if existing and existing.processed:
        logger.info("Paper already processed, skipping", paper_id=str(existing.id))
        return

    # Save paper to DB
    if existing:
        paper = existing
    else:
        paper = Paper(
            subject=paper_info["subject"],
            grade=paper_info.get("grade", "XII"),
            year=paper_info.get("year", ""),
            source_url=paper_info["link"],
            file_path=pdf_path,
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

    # Extract questions (already validated by extract_questions_from_pdf)
    questions = extract_questions_from_pdf(pdf_path)
    logger.info("Extracted questions", count=len(questions))

    # Save questions with embeddings
    for q in questions:
        # Generate embedding
        embedding = None
        if not skip_embeddings:
            try:
                embedding = generate_embedding(q["question_text"])
            except Exception as e:
                logger.warning("Failed to generate embedding", error=str(e))

        question = Question(
            paper_id=paper.id,
            question_number=q.get("question_number"),
            question_text=q["question_text"],
            question_type=q.get("question_type"),
            marks=q.get("marks", 1),
            section=q.get("section"),
            chapter=q.get("chapter"),
            has_diagram=q.get("has_diagram", False),
            embedding=embedding,
        )
        db.add(question)

    # Mark as processed and commit with retry logic
    paper.processed = True
    paper.file_path = pdf_path
    
    # Retry commit up to 3 times to handle connection timeouts
    import time
    for attempt in range(3):
        try:
            db.commit()
            logger.info("Saved to database", paper_id=str(paper.id), questions=len(questions))
            break
        except Exception as e:
            if attempt < 2:  # Don't sleep on last attempt
                logger.warning(f"Commit failed (attempt {attempt + 1}/3), retrying...", error=str(e))
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
                db.rollback()
            else:
                logger.error("Commit failed after 3 attempts", error=str(e))
                db.rollback()
                raise
