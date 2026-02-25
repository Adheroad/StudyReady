"""Coverage planner — ensures balanced chapter, topic, and Bloom's diversity.

Given a pattern template and pools of questions + NCERT chunks,
builds a coverage plan that:
- Maps chapters to sections
- Penalizes overrepresented chapters
- Maintains Bloom's taxonomy diversity
- Avoids near-duplicate embeddings
"""

from collections import Counter, defaultdict
from typing import Optional
import random

from app.core.logging import get_logger
from app.database.models import Question
from app.services.papers.pattern_analyzer import classify_bloom, classify_difficulty

logger = get_logger(__name__)

# Cosine similarity threshold for near-duplicate detection
DUPLICATE_THRESHOLD = 0.92


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not v1 or not v2:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a * a for a in v1) ** 0.5
    norm2 = sum(b * b for b in v2) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def build_chapter_map(questions: list[Question]) -> dict[str, list[Question]]:
    """Group questions by chapter."""
    chapter_map = defaultdict(list)
    for q in questions:
        chapter = q.chapter or q.topic or "General"
        chapter_map[chapter].append(q)
    return dict(chapter_map)


def plan_coverage(
    pattern: dict,
    question_pool: list[Question],
    difficulty: str = "medium",
    ncert_chapters: list[str] | None = None,
) -> dict:
    """
    Build a coverage plan mapping sections to selected questions.

    Algorithm:
    1. Group questions by chapter + marks
    2. For each section in pattern:
       a. Filter candidates by marks range
       b. Sort by least-covered chapters first (weighted sampling)
       c. Apply Bloom's diversity constraint
       d. Apply dedup filter (cosine similarity > threshold → reject)
    3. Return plan with assignments

    Args:
        pattern: Structural template from pattern_analyzer
        question_pool: Available questions from DB
        difficulty: Target difficulty level
        ncert_chapters: Optional list of known NCERT chapters for coverage

    Returns:
        Dict with section assignments and coverage stats
    """
    if not question_pool:
        logger.warning("Empty question pool for coverage planning")
        return {"sections": [], "coverage_stats": {}}

    # Build chapter map
    chapter_map = build_chapter_map(question_pool)
    all_chapters = list(chapter_map.keys())

    # Track coverage across sections
    chapter_coverage = Counter()  # chapter → how many times used
    used_question_ids = set()
    selected_embeddings = []  # For dedup

    # Difficulty mapping for filtering
    difficulty_weights = {
        "easy": {"easy": 0.5, "medium": 0.4, "hard": 0.1},
        "medium": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
        "hard": {"easy": 0.15, "medium": 0.45, "hard": 0.4},
    }
    target_diff = difficulty_weights.get(difficulty, difficulty_weights["medium"])

    section_plans = []

    for section_spec in pattern.get("sections", []):
        section_name = section_spec["name"]
        target_count = section_spec["question_count"]
        target_marks = section_spec["marks_per_question"]
        section_type = section_spec.get("type", "short")

        # Find candidates matching this section's requirements
        candidates = []
        for q in question_pool:
            if q.id in used_question_ids:
                continue

            # Match by marks
            q_marks = q.marks or 1
            if q_marks != target_marks:
                continue

            # Match by type (flexible — allow "short" to match "" or "short")
            q_type = (q.question_type or "").lower()
            if section_type == "mcq" and q_type not in ("mcq", ""):
                continue

            candidates.append(q)

        # Sort candidates: prefer least-covered chapters
        def coverage_score(q):
            chapter = q.chapter or q.topic or "General"
            return chapter_coverage[chapter]

        candidates.sort(key=coverage_score)

        # Select questions with Bloom's diversity
        selected = []
        bloom_counts = Counter()
        target_bloom = pattern.get("bloom_distribution", {})

        for q in candidates:
            if len(selected) >= target_count:
                break

            # Check for near-duplicates
            if q.embedding and selected_embeddings:
                is_dup = False
                for existing_emb in selected_embeddings:
                    if cosine_similarity(list(q.embedding), existing_emb) > DUPLICATE_THRESHOLD:
                        is_dup = True
                        break
                if is_dup:
                    continue

            # Bloom's diversity: soft constraint
            bloom_level = classify_bloom(q.question_text or "")
            bloom_target_ratio = target_bloom.get(bloom_level, 0.2)
            current_ratio = (bloom_counts[bloom_level] / max(len(selected), 1))

            # Allow selection even if over-represented (soft constraint)
            # but prefer under-represented levels
            if current_ratio > bloom_target_ratio * 1.5 and len(candidates) > target_count:
                # Try to skip if we have enough candidates
                continue

            selected.append(q)
            used_question_ids.add(q.id)
            bloom_counts[bloom_level] += 1

            chapter = q.chapter or q.topic or "General"
            chapter_coverage[chapter] += 1

            if q.embedding:
                selected_embeddings.append(list(q.embedding))

        section_plan = {
            "section": section_name,
            "target_count": target_count,
            "selected_count": len(selected),
            "question_ids": [str(q.id) for q in selected],
            "questions": selected,
            "marks_per_question": target_marks,
            "bloom_distribution": dict(bloom_counts),
        }
        section_plans.append(section_plan)

        logger.debug(
            "Section planned",
            section=section_name,
            target=target_count,
            selected=len(selected),
        )

    # Coverage statistics
    total_selected = sum(sp["selected_count"] for sp in section_plans)
    total_target = sum(sp["target_count"] for sp in section_plans)
    chapters_used = len([c for c, count in chapter_coverage.items() if count > 0])

    coverage_stats = {
        "total_selected": total_selected,
        "total_target": total_target,
        "fill_rate": round(total_selected / max(total_target, 1), 2),
        "chapters_covered": chapters_used,
        "total_chapters": len(all_chapters),
        "chapter_coverage": dict(chapter_coverage),
        "difficulty_target": difficulty,
    }

    logger.info(
        "Coverage plan complete",
        fill_rate=coverage_stats["fill_rate"],
        chapters=f"{chapters_used}/{len(all_chapters)}",
    )

    return {
        "sections": section_plans,
        "coverage_stats": coverage_stats,
    }
