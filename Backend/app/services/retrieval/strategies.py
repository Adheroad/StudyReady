"""Enhanced question selection strategies for paper generation."""

from collections import defaultdict
from typing import Optional
import random

from app.database.models import Question
from app.core.logging import get_logger

logger = get_logger(__name__)


def balance_difficulty(
    questions: list[Question],
    target_distribution: Optional[dict] = None,
) -> list[Question]:
    """
    Balance difficulty distribution in selected questions.
    
    Args:
        questions: List of questions to balance
        target_distribution: Dict like {"easy": 0.3, "medium": 0.5, "hard": 0.2}
    
    Returns:
        Balanced list of questions
    """
    if target_distribution is None:
        target_distribution = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
    
    total = len(questions)
    if total == 0:
        return questions
    
    # Group by difficulty
    by_difficulty = defaultdict(list)
    for q in questions:
        difficulty = q.difficulty or "medium"
        by_difficulty[difficulty].append(q)
    
    # Calculate target counts
    targets = {
        diff: int(total * ratio)
        for diff, ratio in target_distribution.items()
    }
    
    # Select questions to match target distribution
    balanced = []
    for difficulty, target_count in targets.items():
        available = by_difficulty.get(difficulty, [])
        selected = available[:target_count]
        balanced.extend(selected)
    
    # Fill remaining slots with any difficulty
    remaining_count = total - len(balanced)
    if remaining_count > 0:
        remaining_pool = [
            q for q in questions
            if q not in balanced
        ]
        balanced.extend(remaining_pool[:remaining_count])
    
    logger.debug(
        "Difficulty balancing",
        input=total,
        output=len(balanced),
        distribution={
            diff: len([q for q in balanced if q.difficulty == diff])
            for diff in target_distribution.keys()
        },
    )
    
    return balanced


def ensure_topic_coverage(
    questions: list[Question],
    min_topics: int = 5,
    max_per_topic: int = 4,
) -> list[Question]:
    """
    Ensure minimum topic diversity in question selection.
    
    Args:
        questions: List of questions
        min_topics: Minimum number of distinct topics
        max_per_topic: Maximum questions from same topic
    
    Returns:
        Filtered list with topic diversity
    """
    topic_counts = defaultdict(int)
    diverse = []
    topics_covered = set()
    
    # First pass: ensure minimum topics
    for q in questions:
        topic = q.topic or "General"
        if topic not in topics_covered or len(topics_covered) < min_topics:
            diverse.append(q)
            topics_covered.add(topic)
            topic_counts[topic] += 1
    
    # Second pass: fill remaining slots respecting max_per_topic
    for q in questions:
        if q in diverse:
            continue
        
        topic = q.topic or "General"
        if topic_counts[topic] < max_per_topic:
            diverse.append(q)
            topic_counts[topic] += 1
    
    logger.debug(
        "Topic coverage filter",
        input=len(questions),
        output=len(diverse),
        topics=len(topics_covered),
        distribution=dict(topic_counts),
    )
    
    return diverse


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


def apply_selection_strategies(
    questions: list[Question],
    enable_difficulty_balance: bool = True,
    enable_topic_coverage: bool = True,
    enable_chapter_diversity: bool = True,
    difficulty_distribution: Optional[dict] = None,
    min_topics: int = 5,
    max_per_chapter: int = 3,
) -> list[Question]:
    """
    Apply all selection strategies in sequence.
    
    Args:
        questions: Input question pool
        enable_*: Flags to enable/disable specific strategies
        difficulty_distribution: Target difficulty distribution
        min_topics: Minimum topics to cover
        max_per_chapter: Max questions per chapter
    
    Returns:
        Filtered and balanced question list
    """
    result = questions.copy()
    
    if enable_chapter_diversity:
        result = ensure_chapter_diversity(result, max_per_chapter)
    
    if enable_topic_coverage:
        result = ensure_topic_coverage(result, min_topics)
    
    if enable_difficulty_balance:
        result = balance_difficulty(result, difficulty_distribution)
    
    logger.info(
        "Selection strategies applied",
        input=len(questions),
        output=len(result),
    )
    
    return result
