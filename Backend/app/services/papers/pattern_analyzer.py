"""Paper pattern analyzer — extracts structural templates from previous papers.

Scans data/papers/ and uses Vision API to extract structural skeletons:
- Section names + question counts
- Marks distribution per section
- OR/choice question positions
- Question types per section
- Difficulty gradient (heuristic)

The output is a JSON template stored in data/patterns/{subject}_{class}.json.
"""

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()
PATTERNS_DIR = Path(settings.DATA_DIR) / "patterns"
PAPERS_DIR = Path(settings.DATA_DIR) / "papers"

# Bloom's taxonomy keyword classifier
BLOOM_KEYWORDS = {
    "remember": [
        "name", "list", "define", "identify", "state", "recall",
        "who", "what", "when", "where", "which",
    ],
    "understand": [
        "explain", "describe", "summarize", "interpret", "classify",
        "discuss", "distinguish", "illustrate",
    ],
    "apply": [
        "calculate", "solve", "demonstrate", "use", "apply",
        "compute", "construct", "show",
    ],
    "analyze": [
        "compare", "contrast", "differentiate", "analyze", "examine",
        "relate", "categorize", "distinguish",
    ],
    "evaluate": [
        "justify", "critique", "evaluate", "assess", "judge",
        "appreciate", "critically",
    ],
    "create": [
        "design", "create", "compose", "formulate", "propose",
        "develop", "plan",
    ],
}


def classify_bloom(text: str) -> str:
    """Classify a question into Bloom's taxonomy level using keyword heuristics."""
    text_lower = text.lower()
    scores = {}
    for level, keywords in BLOOM_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[level] = score

    if max(scores.values()) == 0:
        return "understand"  # Default

    return max(scores, key=scores.get)


def classify_difficulty(marks: int, question_type: str, bloom_level: str) -> str:
    """Heuristic difficulty classification."""
    if marks <= 1:
        return "easy"
    elif marks <= 2:
        if bloom_level in ("analyze", "evaluate", "create"):
            return "medium"
        return "easy"
    elif marks <= 4:
        return "medium"
    else:
        if bloom_level in ("remember", "understand"):
            return "medium"
        return "hard"


def infer_question_type(marks: int, has_options: bool = False) -> str:
    """Infer question type from marks and format."""
    if has_options or marks == 1:
        return "mcq"
    elif marks <= 2:
        return "short"
    elif marks <= 4:
        return "short"
    else:
        return "long"


def extract_pattern_from_questions(questions: list[dict], subject: str, class_level: str) -> dict:
    """
    Extract a structural pattern template from a list of extracted question dicts.

    Args:
        questions: List of question dicts with section, marks, question_type, etc.
        subject: Subject name
        class_level: "X" or "XII" or "10" or "12"

    Returns:
        Pattern template dict.
    """
    # Group questions by section
    sections_data = defaultdict(list)
    for q in questions:
        section = (q.get("section") or "").upper().strip()
        if not section:
            # Infer from marks
            marks = q.get("marks", 1)
            if marks == 1:
                section = "A"
            elif marks <= 3:
                section = "B"
            else:
                section = "C"
        sections_data[section].append(q)

    # Build section templates
    sections = []
    section_titles = {
        "A": ("SECTION – A", "खण्ड – अ", "Multiple Choice Questions", "बहुविकल्पीय प्रश्न"),
        "B": ("SECTION – B", "खण्ड – ब", "Short Answer Type Questions", "लघु उत्तरीय प्रश्न"),
        "C": ("SECTION – C", "खण्ड – स", "Long Answer Type Questions", "दीर्घ उत्तरीय प्रश्न"),
        "D": ("SECTION – D", "खण्ड – द", "Case Study Based Questions", "प्रकरण अध्ययन प्रश्न"),
        "E": ("SECTION – E", "खण्ड – इ", "Map Based Questions", "मानचित्र आधारित प्रश्न"),
    }

    bloom_counts = Counter()
    difficulty_counts = Counter()

    for section_name in sorted(sections_data.keys()):
        qs = sections_data[section_name]
        marks_list = [q.get("marks", 1) for q in qs]
        modal_marks = Counter(marks_list).most_common(1)[0][0]
        types = [q.get("question_type", infer_question_type(q.get("marks", 1))) for q in qs]
        modal_type = Counter(types).most_common(1)[0][0]
        has_or = any(q.get("or_question") for q in qs)

        # Bloom + difficulty for each question
        for q in qs:
            text = q.get("question_text", "")
            bloom = classify_bloom(text)
            diff = classify_difficulty(q.get("marks", 1), modal_type, bloom)
            bloom_counts[bloom] += 1
            difficulty_counts[diff] += 1

        titles = section_titles.get(section_name, (f"SECTION – {section_name}", f"खण्ड – {section_name}", "", ""))

        # Determine instruction text
        if modal_type == "mcq":
            instr_en = f"Attempt all questions. Each question carries {modal_marks} mark(s)."
            instr_hi = f"सभी प्रश्नों के उत्तर दें। प्रत्येक प्रश्न {modal_marks} अंक का है।"
        elif modal_marks <= 3:
            instr_en = "Answer in around 100 words."
            instr_hi = "लगभग 100 शब्दों में उत्तर दें।"
        else:
            instr_en = "Answer in around 300 words."
            instr_hi = "लगभग 300 शब्दों में उत्तर दें।"

        section_template = {
            "name": section_name,
            "title_en": titles[0],
            "title_hi": titles[1],
            "subtitle_en": f"({titles[2]})" if titles[2] else "",
            "subtitle_hi": f"({titles[3]})" if titles[3] else "",
            "type": modal_type,
            "question_count": len(qs),
            "marks_per_question": modal_marks,
            "section_total": sum(marks_list),
            "has_or_questions": has_or,
            "instruction_en": instr_en,
            "instruction_hi": instr_hi,
        }

        if modal_marks >= 4:
            section_template["sub_points_expected"] = 3

        sections.append(section_template)

    total_marks = sum(s["section_total"] for s in sections)
    total_questions = sum(s["question_count"] for s in sections)

    # Normalize distributions
    total_bloom = sum(bloom_counts.values()) or 1
    total_diff = sum(difficulty_counts.values()) or 1

    bloom_dist = {k: round(v / total_bloom, 2) for k, v in bloom_counts.items()}
    diff_dist = {k: round(v / total_diff, 2) for k, v in difficulty_counts.items()}

    # Ensure all difficulty levels present
    for level in ("easy", "medium", "hard"):
        if level not in diff_dist:
            diff_dist[level] = 0.0

    pattern = {
        "subject": subject,
        "class": class_level,
        "total_marks": total_marks,
        "total_questions": total_questions,
        "source_papers_analyzed": 1,
        "last_analyzed": datetime.now(timezone.utc).isoformat(),
        "sections": sections,
        "difficulty_gradient": diff_dist,
        "bloom_distribution": bloom_dist,
    }

    return pattern


def merge_patterns(patterns: list[dict]) -> dict:
    """
    Merge multiple pattern templates into a single modal (most common) pattern.

    Uses the most frequent section structure across all analyzed papers.
    """
    if not patterns:
        return {}
    if len(patterns) == 1:
        return patterns[0]

    # Use the pattern with the most sections as the base
    # (in case some papers extracted poorly)
    base = max(patterns, key=lambda p: len(p.get("sections", [])))
    base["source_papers_analyzed"] = len(patterns)
    base["last_analyzed"] = datetime.now(timezone.utc).isoformat()

    # Average the difficulty/bloom distributions
    diff_keys = set()
    bloom_keys = set()
    for p in patterns:
        diff_keys.update(p.get("difficulty_gradient", {}).keys())
        bloom_keys.update(p.get("bloom_distribution", {}).keys())

    avg_diff = {}
    for k in diff_keys:
        values = [p.get("difficulty_gradient", {}).get(k, 0) for p in patterns]
        avg_diff[k] = round(sum(values) / len(values), 2)

    avg_bloom = {}
    for k in bloom_keys:
        values = [p.get("bloom_distribution", {}).get(k, 0) for p in patterns]
        avg_bloom[k] = round(sum(values) / len(values), 2)

    base["difficulty_gradient"] = avg_diff
    base["bloom_distribution"] = avg_bloom

    return base


def compute_pattern_hash(pattern: dict) -> str:
    """Compute SHA256 hash of the structural portion of a pattern template."""
    # Hash only the structural fields, not timestamps
    hashable = {
        "subject": pattern.get("subject"),
        "class": pattern.get("class"),
        "total_marks": pattern.get("total_marks"),
        "sections": [
            {
                "name": s["name"],
                "type": s["type"],
                "question_count": s["question_count"],
                "marks_per_question": s["marks_per_question"],
            }
            for s in pattern.get("sections", [])
        ],
    }
    return hashlib.sha256(json.dumps(hashable, sort_keys=True).encode()).hexdigest()


def save_pattern(pattern: dict, subject: str, class_level: str) -> Path:
    """Save pattern template to JSON file."""
    PATTERNS_DIR.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r"[^\w]", "_", subject.lower().strip())
    filename = f"{slug}_{class_level}.json"
    filepath = PATTERNS_DIR / filename

    pattern["pattern_hash"] = compute_pattern_hash(pattern)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(pattern, f, indent=2, ensure_ascii=False)

    logger.info("Pattern saved", path=str(filepath), hash=pattern["pattern_hash"])
    return filepath


def load_pattern(subject: str, class_level: str) -> Optional[dict]:
    """
    Load a cached pattern template from JSON file.

    Args:
        subject: Subject name
        class_level: "10", "12", "X", "XII"

    Returns:
        Pattern dict or None if not found.
    """
    # Normalize class level
    class_map = {"X": "10", "XII": "12", "10": "10", "12": "12"}
    normalized_class = class_map.get(class_level, class_level)

    slug = re.sub(r"[^\w]", "_", subject.lower().strip())

    # Try both original and normalized class
    for cls in (class_level, normalized_class):
        filepath = PATTERNS_DIR / f"{slug}_{cls}.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                pattern = json.load(f)
            logger.info("Pattern loaded", path=str(filepath))
            return pattern

    logger.warning("No pattern file found", subject=subject, class_level=class_level)
    return None


def analyze_papers_from_db(db, subject: str, class_level: str) -> dict:
    """
    Analyze papers in the database to extract structural pattern.

    Uses existing extracted questions from the DB (already processed via Vision API).
    """
    from sqlalchemy import select, func
    from app.database.models import Paper, Question

    # Find all processed papers for this subject
    papers_query = (
        select(Paper)
        .where(func.lower(Paper.subject).contains(subject.lower()))
        .where(Paper.processed == True)
    )
    papers = db.execute(papers_query).scalars().all()

    if not papers:
        logger.warning("No processed papers found in DB", subject=subject)
        return {}

    all_patterns = []
    for paper in papers:
        questions_query = select(Question).where(Question.paper_id == paper.id)
        questions = db.execute(questions_query).scalars().all()

        if not questions:
            continue

        q_dicts = [
            {
                "section": q.section or "",
                "marks": q.marks or 1,
                "question_type": q.question_type or "",
                "question_text": q.question_text or "",
                "or_question": None,  # Would need to check parent_question_id
            }
            for q in questions
        ]

        pattern = extract_pattern_from_questions(q_dicts, subject, class_level)
        all_patterns.append(pattern)

    if not all_patterns:
        return {}

    merged = merge_patterns(all_patterns)
    save_pattern(merged, subject, class_level)

    return merged


# Default fallback patterns for subjects without analyzed papers
DEFAULT_PATTERNS = {
    "commercial_art_XII": {
        "subject": "Commercial Art",
        "class": "XII",
        "total_marks": 36,
        "total_questions": 16,
        "source_papers_analyzed": 0,
        "sections": [
            {
                "name": "A",
                "title_en": "SECTION – A",
                "title_hi": "खण्ड – अ",
                "subtitle_en": "(Multiple Choice Questions)",
                "subtitle_hi": "(बहुविकल्पीय प्रश्न)",
                "type": "mcq",
                "question_count": 8,
                "marks_per_question": 1,
                "section_total": 8,
                "has_or_questions": False,
                "instruction_en": "Attempt all questions. Each question carries 1 mark.",
                "instruction_hi": "सभी प्रश्नों के उत्तर दें। प्रत्येक प्रश्न 1 अंक का है।",
            },
            {
                "name": "B",
                "title_en": "SECTION – B",
                "title_hi": "खण्ड – ब",
                "subtitle_en": "(Short Answer Type Questions)",
                "subtitle_hi": "(लघु उत्तरीय प्रश्न)",
                "type": "short",
                "question_count": 5,
                "marks_per_question": 2,
                "section_total": 10,
                "has_or_questions": True,
                "instruction_en": "Answer in around 100 words.",
                "instruction_hi": "लगभग 100 शब्दों में उत्तर दें।",
            },
            {
                "name": "C",
                "title_en": "SECTION – C",
                "title_hi": "खण्ड – स",
                "subtitle_en": "(Long Answer Type Questions)",
                "subtitle_hi": "(दीर्घ उत्तरीय प्रश्न)",
                "type": "long",
                "question_count": 3,
                "marks_per_question": 6,
                "section_total": 18,
                "has_or_questions": True,
                "instruction_en": "Answer in around 300 words.",
                "instruction_hi": "लगभग 300 शब्दों में उत्तर दें।",
                "sub_points_expected": 3,
            },
        ],
        "difficulty_gradient": {"easy": 0.35, "medium": 0.45, "hard": 0.20},
        "bloom_distribution": {
            "remember": 0.25,
            "understand": 0.30,
            "apply": 0.20,
            "analyze": 0.15,
            "evaluate": 0.10,
        },
    }
}


def get_pattern(subject: str, class_level: str, db=None) -> dict:
    """
    Main entry point: get the best available pattern template.

    Priority:
    1. Cached JSON file in data/patterns/
    2. Analyze from DB if papers exist
    3. Default fallback pattern

    Args:
        subject: Subject name
        class_level: Class level
        db: Optional DB session for dynamic analysis

    Returns:
        Pattern template dict.
    """
    # 1. Try cached file
    pattern = load_pattern(subject, class_level)
    if pattern:
        return pattern

    # 2. Try DB analysis
    if db:
        pattern = analyze_papers_from_db(db, subject, class_level)
        if pattern:
            return pattern

    # 3. Fallback to defaults
    class_map = {"X": "10", "XII": "12", "10": "10", "12": "12"}
    normalized = class_map.get(class_level, class_level)
    slug = re.sub(r"[^\w]", "_", subject.lower().strip())
    fallback_key = f"{slug}_{class_level}"

    if fallback_key in DEFAULT_PATTERNS:
        logger.info("Using default pattern", key=fallback_key)
        return DEFAULT_PATTERNS[fallback_key]

    # Ultimate fallback: generic 70-mark paper
    logger.warning("No pattern found, using generic fallback", subject=subject, class_level=class_level)
    return {
        "subject": subject,
        "class": class_level,
        "total_marks": 70,
        "total_questions": 30,
        "source_papers_analyzed": 0,
        "sections": [
            {"name": "A", "type": "mcq", "question_count": 16, "marks_per_question": 1, "section_total": 16, "has_or_questions": False,
             "title_en": "SECTION – A", "title_hi": "खण्ड – अ", "subtitle_en": "(MCQ)", "subtitle_hi": "(बहुविकल्पीय प्रश्न)",
             "instruction_en": "Attempt all questions.", "instruction_hi": "सभी प्रश्नों के उत्तर दें।"},
            {"name": "B", "type": "short", "question_count": 5, "marks_per_question": 2, "section_total": 10, "has_or_questions": True,
             "title_en": "SECTION – B", "title_hi": "खण्ड – ब", "subtitle_en": "(Short Answer)", "subtitle_hi": "(लघु उत्तरीय)",
             "instruction_en": "Answer briefly.", "instruction_hi": "संक्षेप में उत्तर दें।"},
            {"name": "C", "type": "short", "question_count": 6, "marks_per_question": 3, "section_total": 18, "has_or_questions": True,
             "title_en": "SECTION – C", "title_hi": "खण्ड – स", "subtitle_en": "(Short Answer)", "subtitle_hi": "(लघु उत्तरीय)",
             "instruction_en": "Answer in 100 words.", "instruction_hi": "100 शब्दों में उत्तर दें।"},
            {"name": "D", "type": "long", "question_count": 4, "marks_per_question": 5, "section_total": 20, "has_or_questions": True,
             "title_en": "SECTION – D", "title_hi": "खण्ड – द", "subtitle_en": "(Long Answer)", "subtitle_hi": "(दीर्घ उत्तरीय)",
             "instruction_en": "Answer in 250 words.", "instruction_hi": "250 शब्दों में उत्तर दें।", "sub_points_expected": 3},
            {"name": "E", "type": "long", "question_count": 3, "marks_per_question": 4, "section_total": 12, "has_or_questions": True,
             "title_en": "SECTION – E", "title_hi": "खण्ड – इ", "subtitle_en": "(Case Study)", "subtitle_hi": "(प्रकरण अध्ययन)",
             "instruction_en": "Read the passage and answer.", "instruction_hi": "गद्यांश पढ़कर उत्तर दें।"},
        ],
        "difficulty_gradient": {"easy": 0.30, "medium": 0.50, "hard": 0.20},
        "bloom_distribution": {"remember": 0.20, "understand": 0.30, "apply": 0.25, "analyze": 0.15, "evaluate": 0.10},
    }
