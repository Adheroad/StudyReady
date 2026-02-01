"""Pydantic schemas for paper API."""

from typing import Optional

from pydantic import BaseModel, Field


class PaperGenerateRequest(BaseModel):
    """Request schema for paper generation."""

    subject: str = Field(..., description="Subject name (e.g., 'COMMERCIAL ART')")
    grade: str = Field(default="XII", description="Grade level (e.g., 'XII', 'X')")
    year: Optional[str] = Field(default=None, description="Year for paper template (e.g., '2025')")
    language: str = Field(default="en", description="Paper language: 'en', 'hi', or 'both'")
    total_marks: int = Field(default=70, ge=10, le=100, description="Total marks for the paper")
    include_images: bool = Field(default=True, description="Include diagram-based questions")
    section_config: Optional[dict] = Field(
        default=None,
        description="Custom section configuration",
        examples=[{"A": {"marks": 1, "count": 10}, "B": {"marks": 2, "count": 5}}],
    )


class PaperResponse(BaseModel):
    """Response schema for generated paper."""

    paper_id: str = Field(..., description="Unique paper ID")
    subject: str
    grade: str
    year: Optional[str] = None
    language: str = "en"
    total_marks: int
    total_questions: int
    sections: dict = Field(default_factory=dict, description="Section configuration used")
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