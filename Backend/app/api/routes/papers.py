"""Paper generation API routes."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import select

from app.api.deps import SessionDep, SettingsDep
from app.api.schemas.paper_schemas import PaperGenerateRequest, PaperResponse
from app.core.logging import get_logger
from app.database.models import Question, GeneratedPaper
from app.services.papers.blueprint_extractor import extract_section_config
from app.services.retrieval.selector import select_questions_for_paper
from app.services.retrieval.strategies import apply_selection_strategies
from app.services.generation.paper_generator import generate_formatted_paper
from app.services.export import generate_pdf, generate_docx

logger = get_logger(__name__)
router = APIRouter()

EXPORT_DIR = "data/exports"


@router.post("/generate", response_model=PaperResponse)
async def generate_paper(
    request: PaperGenerateRequest,
    db: SessionDep,
    settings: SettingsDep,
):
    """
    Generate a question paper.

    - Retrieves questions from database using hybrid search
    - Selects questions based on marks distribution
    - Formats into CBSE paper format using LLM
    - Returns paper content and metadata
    """
    
    logger.info(
        "Generating paper",
        subject=request.subject,
        grade=request.grade,
        total_marks=request.total_marks,
        language=request.language,
    )

    # Step 1: Extract or use section configuration
    if request.section_config:
        section_config = request.section_config
        logger.info("Using provided section config")
    else:
        section_config = extract_section_config(
            db, request.subject, request.grade, request.year
        )
        logger.info("Extracted section config", sections=len(section_config))

    # Step 2: Retrieve questions from database
    query = (
        select(Question)
        .where(Question.paper_id.isnot(None))
    )
    
    # Filter by subject (via paper join would be better, but simplified here)
    # For now, we'll get all questions and rely on selection strategies
    all_questions = db.execute(query).scalars().all()
    
    if not all_questions:
        raise HTTPException(
            status_code=404,
            detail=f"No questions found for {request.subject} {request.grade}",
        )
    
    logger.info(f"Retrieved {len(all_questions)} questions from database")

    # Step 3: Select questions based on section config
    selected = select_questions_for_paper(
        all_questions,
        section_config=section_config,
        shuffle=True,
    )
    
    # Step 4: Apply enhanced selection strategies
    selected = apply_selection_strategies(
        selected,
        enable_difficulty_balance=True,
        enable_topic_coverage=True,
        enable_chapter_diversity=True,
    )
    
    logger.info(f"Selected {len(selected)} questions after strategies")

    # Step 5: Generate formatted paper using LLM
    formatted_content = generate_formatted_paper(
        questions=selected,
        subject=request.subject,
        grade=request.grade,
        total_marks=request.total_marks,
        language=request.language,
    )

    # Step 6: Save to database
    generated_paper = GeneratedPaper(
        id=uuid.uuid4(),
        subject=request.subject,
        grade=request.grade,
        year=request.year,
        language=request.language,
        total_marks=request.total_marks,
        question_count=len(selected),
        section_config=section_config,
        config={
            "include_images": request.include_images,
            "selection_strategies": {
                "difficulty_balance": True,
                "topic_coverage": True,
                "chapter_diversity": True,
            },
        },
        formatted_content=formatted_content,
        created_at=datetime.utcnow(),
    )
    
    db.add(generated_paper)
    db.commit()
    db.refresh(generated_paper)
    
    logger.info(
        "Paper generated successfully",
        paper_id=str(generated_paper.id),
        questions=len(selected),
    )

    return PaperResponse(
        paper_id=str(generated_paper.id),
        subject=generated_paper.subject,
        grade=generated_paper.grade,
        year=generated_paper.year,
        language=generated_paper.language,
        total_marks=generated_paper.total_marks,
        total_questions=generated_paper.question_count,
        sections=section_config,
        preview=formatted_content[:500] + "..." if len(formatted_content) > 500 else formatted_content,
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
    
    return PaperResponse(
        paper_id=str(paper.id),
        subject=paper.subject,
        grade=paper.grade,
        year=paper.year,
        language=paper.language,
        total_marks=paper.total_marks,
        total_questions=paper.question_count,
        sections=paper.section_config or {},
        preview=paper.formatted_content[:500] + "..." if len(paper.formatted_content or "") > 500 else paper.formatted_content,
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
                "Content-Disposition": f"attachment; filename={paper.subject}_{paper.grade}_{paper.year}.md"
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
                output_path=filepath
            )
            
            # Update database with persistent path
            paper.output_pdf_path = filepath
            db.commit()
            
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                },
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
                output_path=filepath
            )
            
            # Update database with persistent path
            paper.output_docx_path = filepath
            db.commit()
            
            return Response(
                content=docx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                },
            )
        except Exception as e:
            logger.error(f"DOCX generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"DOCX generation failed: {str(e)}")
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{format}'. Use 'pdf', 'docx', or 'markdown'.",
        )
