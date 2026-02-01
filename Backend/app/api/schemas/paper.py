"""Pydantic schemas for paper API."""

from typing import Optional

from pydantic import BaseModel, Field


class PaperGenerateRequest(BaseModel):
    """Request schema for paper generation."""

    subject: str = Field(..., description="Subject name (e.g., 'COMMERCIAL ART')")
    grade: str = Field(default="XII", description="Grade level (e.g., 'XII', 'X')")
    total_marks: int = Field(default=70, ge=10, le=100, description="Total marks for the paper")
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
    total_marks: int
    question_count: int
    paper_text: Optional[str] = Field(None, description="Formatted paper content")
    pdf_path: Optional[str] = Field(None, description="Path to generated PDF")
    docx_path: Optional[str] = Field(None, description="Path to generated DOCX")

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

# TODO extract schema/template from the latest year paper for that subject and adapt the paper response for that to create a more accurate paper generation system.