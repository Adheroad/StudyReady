"""Extract paper blueprint (section structure) from existing papers."""

from collections import defaultdict
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.models import Paper, Question

logger = get_logger(__name__)

# Fallback configuration if no papers exist
# Fallback configuration if no papers exist
# This is a sensible default for a 70-80 mark paper, or can be scaled.
# For Commercial Art (36 marks), we expect 16 questions (8x1, 5x2, 3x6).
DEFAULT_SECTION_CONFIG = {
    "A": {"marks": 1, "count": 16, "type": "mcq"},
    "B": {"marks": 2, "count": 5, "type": "short"},
    "C": {"marks": 6, "count": 3, "type": "long"},
}


def extract_section_config(
    db: Session,
    subject: str,
    grade: str,
    year: Optional[str] = None,
) -> dict:
    """
    Extract section configuration from the latest paper for a subject/grade.
    
    Args:
        db: Database session
        subject: Subject name
        grade: Grade level
        year: Specific year (optional, defaults to latest)
    
    Returns:
        Dict mapping section -> {marks, count, type}
    """
    logger.info(
        "Extracting section config",
        subject=subject,
        grade=grade,
        year=year,
    )
    
    # Find the latest paper for this subject/grade
    query = (
        select(Paper)
        .where(func.lower(Paper.subject) == subject.lower())
        .where(Paper.grade == grade)
        .where(Paper.processed == True)
    )
    
    if year:
        query = query.where(Paper.year == year)
    
    query = query.order_by(Paper.year.desc()).limit(1)
    
    result = db.execute(query)
    paper = result.scalar_one_or_none()
    
    if not paper:
        logger.warning(
            "No papers found, using default config",
            subject=subject,
            grade=grade,
        )
        return DEFAULT_SECTION_CONFIG
    
    # Get all questions for this paper
    questions_query = select(Question).where(Question.paper_id == paper.id)
    questions = db.execute(questions_query).scalars().all()
    
    if not questions:
        logger.warning("Paper has no questions, using default config")
        return DEFAULT_SECTION_CONFIG
    
    # Analyze questions to infer section structure
    section_stats = defaultdict(lambda: {
        "marks": set(),
        "count": 0,
        "types": set(),
    })
    
    for q in questions:
        if not q.section:
            continue
        
        section = q.section.upper()
        section_stats[section]["marks"].add(q.marks)
        section_stats[section]["count"] += 1
        if q.question_type:
            section_stats[section]["types"].add(q.question_type)
    
    # Convert to config format
    config = {}
    for section, stats in sorted(section_stats.items()):
        # Determine most common marks value
        marks_list = list(stats["marks"])
        most_common_marks = max(marks_list, key=marks_list.count) if marks_list else 1
        
        # Determine most common type
        types_list = list(stats["types"])
        most_common_type = types_list[0] if types_list else "short"
        
        config[section] = {
            "marks": most_common_marks,
            "count": stats["count"],
            "type": most_common_type,
        }
    
    logger.info(
        "Section config extracted",
        paper_id=str(paper.id),
        sections=len(config),
        total_questions=sum(s["count"] for s in config.values()),
    )
    
    return config


def calculate_total_marks(section_config: dict) -> int:
    """Calculate total marks from section configuration."""
    return sum(
        section["marks"] * section["count"]
        for section in section_config.values()
    )


def validate_section_config(config: dict) -> bool:
    """
    Validate section configuration structure.
    
    Returns:
        True if valid, False otherwise
    """
    required_keys = {"marks", "count", "type"}
    
    for section, details in config.items():
        if not isinstance(details, dict):
            return False
        if not required_keys.issubset(details.keys()):
            return False
        if not isinstance(details["marks"], int) or details["marks"] <= 0:
            return False
        if not isinstance(details["count"], int) or details["count"] <= 0:
            return False
    
    return True
