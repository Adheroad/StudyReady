"""Database repository for CRUD operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger

from .models import GeneratedPaper, Paper, Question

logger = get_logger(__name__)


class PaperRepository:
    """Repository for Paper CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, subject: str, grade: str, year: str, source_url: str = None) -> Paper:
        """Create a new paper record."""
        paper = Paper(
            subject=subject,
            grade=grade,
            year=year,
            source_url=source_url,
        )
        self.db.add(paper)
        self.db.commit()
        self.db.refresh(paper)
        logger.info("Created paper", paper_id=str(paper.id), subject=subject)
        return paper

    def get_by_id(self, paper_id: UUID) -> Optional[Paper]:
        """Get paper by ID."""
        return self.db.get(Paper, paper_id)

    def get_by_subject(self, subject: str) -> list[Paper]:
        """Get all papers for a subject."""
        stmt = select(Paper).where(Paper.subject.ilike(f"%{subject}%"))
        return list(self.db.execute(stmt).scalars().all())

    def get_unprocessed(self) -> list[Paper]:
        """Get all unprocessed papers."""
        stmt = select(Paper).where(Paper.processed == False)  # noqa: E712
        return list(self.db.execute(stmt).scalars().all())

    def mark_processed(self, paper_id: UUID, file_path: str) -> None:
        """Mark paper as processed."""
        paper = self.get_by_id(paper_id)
        if paper:
            paper.processed = True
            paper.file_path = file_path
            self.db.commit()
            logger.info("Marked paper as processed", paper_id=str(paper_id))


class QuestionRepository:
    """Repository for Question CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        paper_id: UUID,
        question_text: str,
        marks: int,
        question_number: str = None,
        question_type: str = None,
        section: str = None,
        chapter: str = None,
        embedding: list[float] = None,
    ) -> Question:
        """Create a new question record."""
        question = Question(
            paper_id=paper_id,
            question_number=question_number,
            question_text=question_text,
            question_type=question_type,
            marks=marks,
            section=section,
            chapter=chapter,
            embedding=embedding,
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def create_bulk(self, questions: list[dict], paper_id: UUID) -> int:
        """Create multiple questions at once."""
        count = 0
        for q in questions:
            question = Question(
                paper_id=paper_id,
                question_number=q.get("question_number"),
                question_text=q["question_text"],
                question_type=q.get("question_type"),
                marks=q.get("marks", 1),
                section=q.get("section"),
                chapter=q.get("chapter"),
                embedding=q.get("embedding"),
            )
            self.db.add(question)
            count += 1
        self.db.commit()
        logger.info("Created questions in bulk", count=count, paper_id=str(paper_id))
        return count

    def get_by_paper(self, paper_id: UUID) -> list[Question]:
        """Get all questions for a paper."""
        stmt = select(Question).where(Question.paper_id == paper_id)
        return list(self.db.execute(stmt).scalars().all())

    def count_by_subject(self, subject: str) -> int:
        """Count questions for a subject."""
        stmt = (
            select(Question)
            .join(Paper)
            .where(Paper.subject.ilike(f"%{subject}%"))
        )
        return len(list(self.db.execute(stmt).scalars().all()))


class GeneratedPaperRepository:
    """Repository for GeneratedPaper operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        subject: str,
        grade: str,
        total_marks: int,
        question_count: int,
        config: dict = None,
        output_pdf_path: str = None,
        output_docx_path: str = None,
    ) -> GeneratedPaper:
        """Create a generated paper record."""
        paper = GeneratedPaper(
            subject=subject,
            grade=grade,
            total_marks=total_marks,
            question_count=question_count,
            config=config,
            output_pdf_path=output_pdf_path,
            output_docx_path=output_docx_path,
        )
        self.db.add(paper)
        self.db.commit()
        self.db.refresh(paper)
        logger.info("Created generated paper", paper_id=str(paper.id))
        return paper
