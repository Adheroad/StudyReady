"""Pydantic schemas for question API."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionBase(BaseModel):
    """Base question schema."""

    question_number: Optional[str] = None
    question_text: str
    question_type: Optional[str] = Field(None, description="mcq, short, long, practical")
    marks: int = Field(..., ge=1, le=20)
    section: Optional[str] = Field(None, description="Section A, B, C, D")
    chapter: Optional[str] = None


class QuestionResponse(QuestionBase):
    """Response schema for questions."""

    id: UUID
    paper_id: Optional[UUID] = None
    difficulty: Optional[str] = None
    has_diagram: bool = False

    class Config:
        from_attributes = True


class QuestionSearchRequest(BaseModel):
    """Request schema for question search."""

    query: Optional[str] = Field(None, description="Semantic search query")
    subject: Optional[str] = None
    marks: Optional[int] = None
    section: Optional[str] = None
    question_type: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class QuestionCreate(QuestionBase):
    """Schema for creating a question."""

    paper_id: UUID
    embedding: Optional[list[float]] = None
