"""Question selector for building balanced question papers."""

from typing import Optional
from collections import defaultdict
import random

from app.database.models import Question
from app.core.logging import get_logger

logger = get_logger(__name__)

# Default CBSE paper configuration
DEFAULT_SECTION_CONFIG = {
    "A": {"marks": 1, "count": 16, "type": "mcq"},
    "B": {"marks": 2, "count": 5, "type": "short"},
    "C": {"marks": 3, "count": 6, "type": "short"},
    "D": {"marks": 5, "count": 4, "type": "long"},
    "E": {"marks": 4, "count": 3, "type": "case_study"},
}
# TODO again above todo is not correct we may need to process the latest year paper for that subject to get the accurate section config.


def select_questions_for_paper(
    questions: list[Question],
    section_config: Optional[dict] = None,
    shuffle: bool = True,
) -> list[Question]:
    """
    Select questions for a balanced paper based on section requirements.

    Args:
        questions: Pool of available questions
        section_config: Dict mapping section -> {marks, count, type}
        shuffle: Whether to shuffle selection for variety

    Returns:
        List of selected questions organized by section
    """
    if section_config is None:
        section_config = DEFAULT_SECTION_CONFIG

    selected = []
    used_ids = set()

    # Group questions by section and marks
    by_section = defaultdict(list)
    by_marks = defaultdict(list)

    for q in questions:
        if q.section:
            by_section[q.section].append(q)
        if q.marks:
            by_marks[q.marks].append(q)

    for section, config in section_config.items():
        target_count = config["count"]
        target_marks = config.get("marks")
        target_type = config.get("type")

        # Get candidates from section or by marks
        candidates = by_section.get(section, [])

        # If not enough in section, try by marks
        if len(candidates) < target_count and target_marks:
            candidates = [
                q for q in by_marks.get(target_marks, [])
                if q.id not in used_ids
            ]

        # Filter by type if specified
        if target_type:
            candidates = [
                q for q in candidates
                if q.question_type == target_type or not q.question_type
            ]

        # Remove already used
        candidates = [q for q in candidates if q.id not in used_ids]

        # Shuffle for variety
        if shuffle:
            random.shuffle(candidates)

        # Select up to target count
        section_selected = candidates[:target_count]

        for q in section_selected:
            selected.append(q)
            used_ids.add(q.id)

        logger.debug(
            "Section selection",
            section=section,
            target=target_count,
            selected=len(section_selected),
        )

    logger.info(
        "Paper selection complete",
        total_selected=len(selected),
        total_marks=sum(q.marks or 0 for q in selected),
    )

    return selected


def calculate_paper_statistics(questions: list[Question]) -> dict:
    """
    Calculate statistics for a question set.

    Returns:
        Dict with total_marks, section_breakdown, type_breakdown
    """
    stats = {
        "total_questions": len(questions),
        "total_marks": 0,
        "by_section": defaultdict(lambda: {"count": 0, "marks": 0}),
        "by_type": defaultdict(int),
    }

    for q in questions:
        marks = q.marks or 0
        stats["total_marks"] += marks

        section = q.section or "Unknown"
        stats["by_section"][section]["count"] += 1
        stats["by_section"][section]["marks"] += marks

        qtype = q.question_type or "unknown"
        stats["by_type"][qtype] += 1

    # Convert defaultdicts to regular dicts for JSON serialization
    stats["by_section"] = dict(stats["by_section"])
    stats["by_type"] = dict(stats["by_type"])

    return stats


def ensure_chapter_diversity(
    questions: list[Question],
    max_per_chapter: int = 3,
) -> list[Question]:
    """
    Filter questions to ensure chapter diversity.

    Args:
        questions: List of questions
        max_per_chapter: Maximum questions from same chapter

    Returns:
        Filtered list with chapter diversity
    """
    chapter_counts = defaultdict(int)
    diverse = []

    for q in questions:
        chapter = q.chapter or "Unknown"
        if chapter_counts[chapter] < max_per_chapter:
            diverse.append(q)
            chapter_counts[chapter] += 1

    logger.debug(
        "Chapter diversity filter",
        input=len(questions),
        output=len(diverse),
        chapters=len(chapter_counts),
    )

    return diverse

# TODO we might want to add more selection strategies like difficulty balancing, topic coverage etc. also as there are changes in our RAG system we might want to revisit these selection strategies to see if they need any updates.