"""Paper generation API routes — simplified pipeline-based generation."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import select

from app.api.deps import SessionDep, SettingsDep
from app.api.schemas.paper_schemas import PaperGenerateRequest, PaperResponse
from app.core.logging import get_logger
from app.database.models import GeneratedPaper
from app.services.generation.pipeline import generate_paper_pipeline
from app.services.export import generate_pdf, generate_docx

logger = get_logger(__name__)
router = APIRouter()

EXPORT_DIR = "data/exports"


@router.post("/generate", response_model=PaperResponse)
async def generate_paper(
    subject: str,
    target_class: str,
    db: SessionDep,
    settings: SettingsDep,
    difficulty: str = "medium",
    pattern: str = "auto",
    marks: int = 30,
    language: str = "both",
):
    """
    Generate a question paper using the full pipeline.

    Simplified API — no manual section_config needed:
    1. Auto-resolves pattern template from analyzed previous papers
    2. Retrieves NCERT content for grounding
    3. Generates via LLM with structural constraints
    4. Self-validates and auto-corrects
    5. Returns validated paper
    """

    logger.info(
        "Generating paper via pipeline",
        subject=subject,
        target_class=target_class,
        difficulty=difficulty,
    )

    try:
        generated_paper = generate_paper_pipeline(
            db=db,
            subject=subject,
            target_class=target_class,
            difficulty=difficulty,
            pattern_id=pattern,
            marks=marks,
            language=language,
        )
    except Exception as e:
        logger.error("Pipeline failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Paper generation failed: {str(e)}")

    content = generated_paper.formatted_content or ""
    return PaperResponse(
        paper_id=str(generated_paper.id),
        subject=generated_paper.subject,
        grade=generated_paper.grade,
        year=generated_paper.year,
        language=generated_paper.language,
        total_marks=generated_paper.total_marks,
        total_questions=generated_paper.question_count or 0,
        sections=generated_paper.section_config or {},
        validation=generated_paper.validation_result,
        preview=content[:500] + "..." if len(content) > 500 else content,
        created_at=generated_paper.created_at.isoformat(),
    )


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: str, db: SessionDep):
    """Get a generated paper by ID."""

    try:
        paper_uuid = uuid.UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper ID format")

    query = select(GeneratedPaper).where(GeneratedPaper.id == paper_uuid)
    result = db.execute(query)
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    content = paper.formatted_content or ""
    return PaperResponse(
        paper_id=str(paper.id),
        subject=paper.subject,
        grade=paper.grade,
        year=paper.year,
        language=paper.language,
        total_marks=paper.total_marks,
        total_questions=paper.question_count or 0,
        sections=paper.section_config or {},
        validation=paper.validation_result,
        preview=content[:500] + "..." if len(content) > 500 else content,
        created_at=paper.created_at.isoformat(),
    )


@router.get("/{paper_id}/download")
async def download_paper(paper_id: str, format: str = "pdf", db: SessionDep = None):
    """Download generated paper as PDF, DOCX, or Markdown."""
    try:
        paper_uuid = uuid.UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper ID format")

    query = select(GeneratedPaper).where(GeneratedPaper.id == paper_uuid)
    result = db.execute(query)
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    format_lower = format.lower()

    # Markdown format
    if format_lower in ["markdown", "md"]:
        return Response(
            content=paper.formatted_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={paper.subject}_{paper.grade}.md"
            },
        )
    # PDF format
    elif format_lower == "pdf":
        try:
            filename = f"{paper.subject}_{paper.id}.pdf".replace(" ", "_")
            filepath = f"{EXPORT_DIR}/{filename}"

            pdf_bytes = generate_pdf(
                paper_content=paper.formatted_content,
                subject=paper.subject,
                grade=paper.grade,
                total_marks=paper.total_marks,
                output_path=filepath,
            )

            paper.output_pdf_path = filepath
            db.commit()

            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    # DOCX format
    elif format_lower in ["docx", "doc"]:
        try:
            filename = f"{paper.subject}_{paper.id}.docx".replace(" ", "_")
            filepath = f"{EXPORT_DIR}/{filename}"

            docx_bytes = generate_docx(
                paper_content=paper.formatted_content,
                subject=paper.subject,
                grade=paper.grade,
                total_marks=paper.total_marks,
                output_path=filepath,
            )

            paper.output_docx_path = filepath
            db.commit()

            return Response(
                content=docx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except Exception as e:
            logger.error(f"DOCX generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"DOCX generation failed: {str(e)}")

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{format}'. Use 'pdf', 'docx', or 'markdown'.",
        )
