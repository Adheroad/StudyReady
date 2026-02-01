#!/usr/bin/env python3
"""
RAG Ingestion Pipeline - Download, extract, embed, and store CBSE papers.

Usage:
    python scripts/ingest_papers.py --subject "mathematics" --grade 12 --limit 5
    python scripts/ingest_papers.py --subject "physics" --year 2024
    python scripts/ingest_papers.py --pdf /path/to/paper.pdf --subject "chemistry" --grade 12 --year 2024
"""

import argparse
import sys
import uuid
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database.connection import SessionLocal, engine
from app.database.models import Base, Paper, Question
from app.services.papers.cbse_scraper import get_papers_by_subject
from app.services.papers.downloader import download_paper
from app.services.extraction.gemini_vision import extract_questions_from_pdf
from app.services.embeddings.gemini_embeddings import generate_embedding

setup_logging(log_level="INFO", debug=True)
logger = get_logger(__name__)
settings = get_settings()


def create_tables():
    """Ensure database tables exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")


def ingest_single_pdf(
    db: Session,
    pdf_path: str,
    subject: str,
    grade: str,
    year: str,
    subject_code: str | None = None,
) -> tuple[Paper, list[Question]]:
    """
    Ingest a single PDF file into the database.

    Args:
        db: Database session
        pdf_path: Path to PDF file
        subject: Subject name
        grade: Grade level
        year: Year of paper
        subject_code: Optional subject code

    Returns:
        Tuple of (Paper, list of Questions)
    """
    logger.info("Ingesting PDF", path=pdf_path, subject=subject)

    # Create paper record
    paper = Paper(
        id=uuid.uuid4(),
        subject=subject,
        subject_code=subject_code,
        grade=grade,
        year=year,
        file_path=pdf_path,
        processed=False,
    )
    db.add(paper)
    db.flush()  # Get paper ID

    # Extract questions using Vision API
    logger.info("Extracting questions from PDF...")
    try:
        extracted = extract_questions_from_pdf(pdf_path)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        db.rollback()
        raise

    questions = []
    for q_data in extracted:
        # Generate embedding for question text
        q_text = q_data.get("question_text", "")
        if not q_text:
            continue

        logger.debug("Generating embedding", question=q_text[:50])
        try:
            embedding = generate_embedding(q_text)
        except Exception as e:
            logger.warning(f"Embedding failed for question: {e}")
            embedding = None

        question = Question(
            id=uuid.uuid4(),
            paper_id=paper.id,
            question_number=q_data.get("question_number", ""),
            question_text=q_text,
            question_type=q_data.get("question_type", "short"),
            marks=q_data.get("marks", 1),
            section=q_data.get("section", ""),
            chapter=q_data.get("chapter", ""),
            topic=q_data.get("topic", ""),
            difficulty=q_data.get("difficulty", "medium"),
            language=q_data.get("language", "en"),
            has_diagram=q_data.get("has_diagram", False),
            image_path=q_data.get("image_path"),
            image_description=q_data.get("image_description"),
            embedding=embedding,
        )
        questions.append(question)
        db.add(question)

    paper.processed = True
    db.commit()

    logger.info(
        "Ingestion complete",
        paper_id=str(paper.id),
        questions=len(questions),
    )

    return paper, questions


def ingest_from_cbse(
    db: Session,
    subject: str,
    grade: str | None = None,
    year: str | None = None,
    limit: int = 5,
    force: bool = False,
    subject_code: str | None = None,
) -> list[Paper]:
    """
    Scrape and ingest papers from CBSE website.

    Args:
        db: Database session
        subject: Subject to search
        grade: Optional grade filter
        year: Optional year filter
        limit: Max papers to process
        force: If True, overwrite existing papers
        subject_code: Optional subject code to assign

    Returns:
        List of ingested Paper objects
    """
    logger.info("Fetching papers from CBSE", subject=subject, limit=limit)

    # Get paper URLs from scraper
    papers_data = get_papers_by_subject(subject, grade=grade, year=year)

    if not papers_data:
        logger.warning("No papers found for subject", subject=subject)
        return []

    papers_data = papers_data[:limit]
    ingested = []

    for i, paper_info in enumerate(papers_data, 1):
        logger.info(f"Processing paper {i}/{len(papers_data)}", **paper_info)

        try:
            # Check if paper already exists
            existing_paper = db.query(Paper).filter(
                Paper.subject == subject,
                Paper.year == paper_info.get("year", year or "Unknown"),
                Paper.grade == paper_info.get("grade", grade or "Unknown")
            ).first()

            if existing_paper:
                if force:
                    logger.info("Force re-ingesting paper: deleting existing record", paper_id=str(existing_paper.id))
                    db.delete(existing_paper)
                    db.commit()
                else:
                    logger.info("Skipping existing paper (use --force to re-ingest)", paper_id=str(existing_paper.id))
                    continue

            # Download PDF
            # Update paper info with CLI args if needed (though scraper result is usually best)
            # But the scraper result might miss explicit overrides if we wanted them.
            # Here we just pass the scraper result as it's sufficient.
            pdf_path = download_paper(paper_info)

            if not pdf_path:
                logger.warning("Download failed", url=paper_info["link"])
                continue

            # Ingest the PDF
            paper, questions = ingest_single_pdf(
                db=db,
                pdf_path=pdf_path,
                subject=subject,
                grade=paper_info.get("grade", grade or "Unknown"),
                year=paper_info.get("year", year or "Unknown"),
                subject_code=subject_code,
            )
            ingested.append(paper)

        except Exception as e:
            logger.error(f"Failed to process paper: {e}")
            continue

    logger.info("CBSE ingestion complete", total=len(ingested))
    return ingested


# QQ no print statments, use logger instead
def main():
    parser = argparse.ArgumentParser(
        description="RAG Ingestion Pipeline for CBSE Papers"
    )
    parser.add_argument(
        "--subject",
        required=True,
        help="Subject name (e.g., 'mathematics', 'physics')",
    )
    parser.add_argument(
        "--grade",
        default=None,
        help="Grade level (e.g., '10', '12')",
    )
    parser.add_argument(
        "--year",
        default=None,
        help="Year filter (e.g., '2024')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum papers to process (default: 5)",
    )
    parser.add_argument(
        "--pdf",
        default=None,
        help="Path to a local PDF file to ingest",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion of existing papers",
    )

    parser.add_argument(
        "--subject-code",
        default=None,
        help="Subject code (e.g., '052' for Comm Art)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("CBSE RAG Ingestion Pipeline")
    print("=" * 60 + "\n")

    # Ensure tables exist
    create_tables()

    db = SessionLocal()
    try:
        if args.pdf:
            # Ingest single PDF
            if not Path(args.pdf).exists():
                print(f"Error: PDF not found: {args.pdf}")
                sys.exit(1)

            paper, questions = ingest_single_pdf(
                db=db,
                pdf_path=args.pdf,
                subject=args.subject,
                grade=args.grade or "Unknown",
                year=args.year or "Unknown",
                subject_code=args.subject_code,
            )
            print(f"\n✓ Ingested paper: {paper.id}")
            print(f"  Questions extracted: {len(questions)}")

        else:
            # Scrape and ingest from CBSE
            papers = ingest_from_cbse(
                db=db,
                subject=args.subject,
                grade=args.grade,
                year=args.year,
                limit=args.limit,
                force=args.force,
                subject_code=args.subject_code,
            )
            print(f"\n✓ Ingested {len(papers)} papers")
            for p in papers:
                print(f"  - {p.subject} ({p.grade}, {p.year}): {p.id}")

    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("Ingestion complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
