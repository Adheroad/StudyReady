#!/usr/bin/env python3
"""
Extract questions from CBSE papers and store in database.

Usage:
    python scripts/extract_papers.py --subject "commercial art" --limit 8
    python scripts/extract_papers.py --subject design --grade XII --year 2024
"""

import argparse
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database.connection import SessionLocal
from app.database.models import Paper, Question
from app.services.embeddings.gemini_embeddings import generate_embedding
from app.services.extraction.gemini_vision import (
    extract_questions_from_pdf,
    validate_extracted_questions,
)
from app.services.papers.cbse_scraper import get_papers_by_subject
from app.services.papers.downloader import download_paper

# Setup logging first
settings = get_settings()
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    debug=settings.DEBUG,
)
logger = get_logger(__name__)


def main(
    subject: str,
    grade: str = None,
    year: str = None,
    limit: int = None,
    skip_embeddings: bool = False,
):
    """Main extraction pipeline."""
    logger.info(
        "Starting extraction",
        subject=subject,
        grade=grade,
        year=year,
        limit=limit,
    )

    db = SessionLocal()
    processed_count = 0
    error_count = 0

    try:
        # Fetch papers
        papers = get_papers_by_subject(subject, grade, year)

        if not papers:
            logger.warning("No papers found", subject=subject)
            return

        if limit:
            papers = papers[:limit]

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

## no silent failures, log everything
    finally:
        db.close()


def _process_single_paper(db, paper_info: dict, skip_embeddings: bool = False) -> None:
    """Process a single paper: download, extract, store."""
    # Download
    pdf_path = download_paper(paper_info)
    logger.debug("Downloaded paper", path=pdf_path)

    # Check if already processed
    existing = (
        db.query(Paper)
        .filter(
            Paper.subject == paper_info["subject"],
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

    # Extract questions
    raw_questions = extract_questions_from_pdf(pdf_path)
    questions = validate_extracted_questions(raw_questions)
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

    paper.processed = True
    paper.file_path = pdf_path
    db.commit()
    logger.info("Saved to database", paper_id=str(paper.id), questions=len(questions))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract CBSE papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/extract_papers.py --subject "commercial art" --limit 2
  python scripts/extract_papers.py --subject "fine arts" --grade XII
  python scripts/extract_papers.py --subject design --year 2024 --skip-embeddings
        """,
    )
    parser.add_argument(
        "--subject",
        required=True,
        help="Subject name filter (case-insensitive partial match)",
    )
    parser.add_argument("--grade", help="Grade filter (e.g., XII, X)")
    parser.add_argument("--year", help="Year filter (e.g., 2024)")
    parser.add_argument("--limit", type=int, help="Max papers to process")
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip embedding generation (faster for testing)",
    )

    args = parser.parse_args()
    main(args.subject, args.grade, args.year, args.limit, args.skip_embeddings)
