"""SQLAlchemy ORM models for the question paper generator."""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .connection import Base


class Paper(Base):
    """Model for source CBSE papers."""

    __tablename__ = "papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject = Column(String(100), nullable=False, index=True)
    subject_code = Column(String(10), nullable=True)
    grade = Column(String(10), nullable=False, index=True)
    year = Column(String(20), nullable=False, index=True)
    paper_type = Column(String(50), default="main")
    source_url = Column(Text)
    file_path = Column(Text)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to questions
    questions = relationship("Question", back_populates="paper", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Paper {self.subject} {self.year} Grade {self.grade}>"


class Question(Base):
    """Model for extracted questions with embeddings."""

    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"))
    question_number = Column(String(50))
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # mcq, short, long, practical
    marks = Column(Integer, nullable=False)
    section = Column(String(50))  # A, B, C, D
    chapter = Column(String(200))
    topic = Column(String(300))
    difficulty = Column(String(50))  # easy, medium, hard
    language = Column(String(10), default="en")  # en, hi
    parent_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)  # Link translations
    answer_key = Column(Text)
    has_diagram = Column(Boolean, default=False)
    image_path = Column(Text, nullable=True)  # Path to extracted crop
    image_description = Column(Text, nullable=True)  # AI description
    embedding = Column(Vector(1536))  # OpenAI embedding-3-small dimension
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to paper
    paper = relationship("Paper", back_populates="questions")

    def __repr__(self) -> str:
        return f"<Question {self.question_number} ({self.marks} marks)>"


class GeneratedPaper(Base):
    """Model for tracking generated question papers."""

    __tablename__ = "generated_papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject = Column(String(100), nullable=False)
    grade = Column(String(10), nullable=False)
    year = Column(String(20))  # Year for which paper is generated
    language = Column(String(10), default="en")  # en, hi, or both
    total_marks = Column(Integer)
    question_count = Column(Integer)
    section_config = Column(JSONB)  # Section structure used
    config = Column(JSONB)  # Store generation parameters
    formatted_content = Column(Text)  # Markdown formatted paper
    output_pdf_path = Column(Text)
    output_docx_path = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<GeneratedPaper {self.subject} {self.total_marks} marks>"
