"""Pydantic schemas for paper API."""

from typing import Optional

from pydantic import BaseModel, Field


class PaperGenerateRequest(BaseModel):
    """Simplified request schema for paper generation.

    No manual section_config needed — the system automatically
    resolves the structural pattern from analyzed previous papers.
    """

    subject: str = Field(..., description="Subject name (e.g., 'Commercial Art')")
    target_class: str = Field(..., description="Class: '10' or '12'")
    difficulty: str = Field(
        default="medium",
        description="Difficulty level: 'easy', 'medium', or 'hard'",
    )
    pattern: str = Field(
        default="auto",
        description="Pattern resolution: 'auto' (recommended) or specific pattern hash",
    )
    marks: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Total marks override. 0 = auto-detect from pattern.",
    )
    language: str = Field(
        default="both",
        description="Paper language: 'en', 'hi', or 'both'",
    )


class PaperResponse(BaseModel):
    """Response schema for generated paper."""

    paper_id: str = Field(..., description="Unique paper ID")
    subject: str
    grade: str
    year: Optional[str] = None
    language: str = "both"
    total_marks: int
    total_questions: int
    sections: dict = Field(default_factory=dict, description="Section configuration used")
    validation: Optional[dict] = Field(None, description="Validation result")
    preview: Optional[str] = Field(None, description="Preview of formatted paper content")
    created_at: str

    class Config:
        from_attributes = True


class PaperListItem(BaseModel):
    """Schema for paper list item."""

    id: str
    subject: str
    grade: str
    year: str
    processed: bool

    class Config:
        from_attributes = True