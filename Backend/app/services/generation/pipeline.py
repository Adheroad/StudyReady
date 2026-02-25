"""Pipeline orchestrator — ties pattern resolution, retrieval, coverage,
generation, validation, and formatting into a single entry point.

Usage:
    result = generate_paper_pipeline(request, db)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.config import get_settings
from app.core.logging import get_logger
from app.database.models import Paper, Question, GeneratedPaper
from app.services.papers.pattern_analyzer import get_pattern, compute_pattern_hash
from app.services.retrieval.coverage_planner import plan_coverage
from app.services.retrieval.search import hybrid_search, search_ncert_content

logger = get_logger(__name__)
settings = get_settings()


def _build_section_blueprint(pattern: dict) -> str:
    """Convert pattern sections to a readable blueprint string for the prompt."""
    lines = ["| Section | Questions | Marks Each | Total | Type | OR? |"]
    lines.append("|---------|-----------|------------|-------|------|-----|")

    for s in pattern.get("sections", []):
        lines.append(
            f"| **{s['name']}** | {s['question_count']} | "
            f"{s['marks_per_question']} | {s['section_total']} | "
            f"{s['type'].upper()} | {'Yes' if s.get('has_or_questions') else 'No'} |"
        )

    total = pattern.get("total_marks", 0)
    total_q = sum(s["question_count"] for s in pattern.get("sections", []))
    lines.append(f"| **Total** | {total_q} | — | **{total}** | — | — |")

    # Add section-specific instructions
    lines.append("\n### Section Details:")
    for s in pattern.get("sections", []):
        lines.append(f"- **{s['name']}** ({s.get('title_en', '')}): {s.get('instruction_en', '')}")
        if s.get("has_or_questions"):
            lines.append(f"  - Each question must have an OR alternative")
        if s.get("sub_points_expected"):
            lines.append(f"  - Each question should have {s['sub_points_expected']} sub-points")

    return "\n".join(lines)


def _get_ncert_context(db: Session, subject: str, target_class: str = "12", limit: int = 15) -> str:
    """Retrieve NCERT content chunks for the prompt."""
    # 1. Search actual textbook chunks
    chunks = search_ncert_content(
        db=db,
        query=f"{subject} syllabus and textbook concepts",
        subject=subject,
        target_class=target_class,
        limit=limit,
    )

    if chunks:
        context = []
        for c in chunks:
            # Metadata might contain chapter title or number
            meta = c.chunk_metadata or {}
            chapter = meta.get("chapter_num", "Chapter")
            context.append(f"[NCERT {subject} Ch {chapter}] {c.content[:400]}")
        return "\n".join(context)

    # 2. Fallback: Search for NCERT-related questions in previous papers
    ncert_questions = hybrid_search(
        db=db,
        query=f"{subject} NCERT textbook concepts",
        subject=subject,
        limit=limit,
    )

    if not ncert_questions:
        return "(No NCERT content available — generate based on standard CBSE syllabus knowledge.)"

    q_chunks = []
    for q in ncert_questions:
        text = q.question_text or ""
        if text:
            chapter = q.chapter or q.topic or "General"
            q_chunks.append(f"[Reference] {text[:300]}")

    return "\n".join(q_chunks[:limit])


def _get_paper_examples(db: Session, subject: str, limit: int = 10) -> str:
    """Retrieve previous paper question examples for style priors."""
    questions = hybrid_search(
        db=db,
        subject=subject,
        limit=limit,
    )

    if not questions:
        return "(No previous paper examples available.)"

    examples = []
    for q in questions:
        text = q.question_text or ""
        marks = q.marks or 1
        section = q.section or "?"
        examples.append(f"[Section {section}, {marks} marks] {text[:200]}")

    return "\n".join(examples[:limit])


def generate_paper_pipeline(
    db: Session,
    subject: str,
    target_class: str,
    difficulty: str = "medium",
    pattern_id: str = "auto",
    marks: int = 0,
    language: str = "both",
) -> GeneratedPaper:
    """
    Full pipeline: Pattern → Retrieve → Plan → Generate → Validate → Store.

    Args:
        db: Database session
        subject: Subject name
        target_class: "10" or "12"
        difficulty: "easy", "medium", or "hard"
        pattern_id: "auto" or specific pattern path
        marks: 0 = auto from pattern, else override
        language: "en", "hi", or "both"

    Returns:
        GeneratedPaper model instance (saved to DB).
    """
    from openai import OpenAI
    from app.core.prompts import load_prompt
    from app.services.generation.validator import validate_paper, build_fix_prompt

    logger.info(
        "Pipeline started",
        subject=subject,
        target_class=target_class,
        difficulty=difficulty,
    )

    # ─── Stage 1: Resolve Pattern ───
    class_map = {"10": "X", "12": "XII"}
    class_roman = class_map.get(target_class, target_class)

    pattern = get_pattern(subject, target_class, db=db)
    if marks > 0:
        # Override total marks but keep section ratios
        pattern["total_marks"] = marks

    pattern_hash = compute_pattern_hash(pattern)
    total_marks = pattern.get("total_marks", 70)

    logger.info("Pattern resolved", hash=pattern_hash[:12], total_marks=total_marks)

    # ─── Stage 2: Retrieve Content ───
    if settings.ENABLE_NCERT_RAG:
        ncert_context = _get_ncert_context(db, subject, target_class=target_class)
    else:
        logger.info("NCERT RAG disabled via settings")
        ncert_context = "(NCERT RAG is disabled. Generate based on standard CBSE syllabus knowledge.)"
        
    paper_examples = _get_paper_examples(db, subject)

    # ─── Stage 3: Build Prompt ───
    prompt_template = load_prompt("paper_generation")
    section_blueprint = _build_section_blueprint(pattern)

    diff_gradient = pattern.get("difficulty_gradient", {"easy": 0.3, "medium": 0.5, "hard": 0.2})

    # Build subject names
    subject_en = subject.upper()
    subject_hi = subject  # Will be translated by LLM

    prompt = prompt_template.format(
        subject=subject,
        class_level=class_roman,
        language=language,
        total_marks=total_marks,
        difficulty=difficulty,
        section_blueprint=section_blueprint,
        ncert_context=ncert_context,
        paper_examples=paper_examples,
        diff_easy=int(diff_gradient.get("easy", 0.3) * 100),
        diff_medium=int(diff_gradient.get("medium", 0.5) * 100),
        diff_hard=int(diff_gradient.get("hard", 0.2) * 100),
        subject_en=subject_en,
        subject_hi=subject_hi,
    )

    # ─── Stage 4: Generate via LLM ───
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
        timeout=90.0,
    )

    logger.info("Calling LLM for paper generation")

    response = client.chat.completions.create(
        model=settings.GENERATION_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert CBSE question paper designer. "
                    "Return ONLY a valid JSON object matching the specified schema. "
                    "No explanations, no markdown code fences."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=settings.GENERATION_TEMPERATURE,
        top_p=settings.GENERATION_TOP_P,
        frequency_penalty=settings.GENERATION_FREQUENCY_PENALTY,
        presence_penalty=settings.GENERATION_PRESENCE_PENALTY,
        max_tokens=settings.GENERATION_MAX_TOKENS,
        response_format={"type": "json_object"},
    )

    raw_content = response.choices[0].message.content.strip()

    # Clean markdown wrappers
    if raw_content.startswith("```"):
        raw_content = raw_content.replace("```json", "").replace("```", "").strip()

    logger.info("LLM response received", length=len(raw_content))

    # ─── Stage 5: Validate ───
    validation = validate_paper(raw_content, pattern)

    # Self-healing: retry if validation fails (up to 2 attempts)
    if not validation["valid"]:
        logger.warning("Validation failed, attempting fix", errors=validation["errors"])

        for attempt in range(2):
            fix_prompt = build_fix_prompt(validation, raw_content)
            if not fix_prompt:
                break

            fix_response = client.chat.completions.create(
                model=settings.GENERATION_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Fix the JSON paper structure. Return ONLY corrected JSON.",
                    },
                    {"role": "user", "content": fix_prompt},
                ],
                temperature=0.1,
                max_tokens=settings.GENERATION_MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            raw_content = fix_response.choices[0].message.content.strip()
            if raw_content.startswith("```"):
                raw_content = raw_content.replace("```json", "").replace("```", "").strip()

            validation = validate_paper(raw_content, pattern)

            if validation["valid"]:
                logger.info("Paper fixed on attempt", attempt=attempt + 1)
                break
            else:
                logger.warning("Fix attempt failed", attempt=attempt + 1, errors=validation["errors"])

    # ─── Stage 6: Store ───
    generated_paper = GeneratedPaper(
        id=uuid.uuid4(),
        subject=subject,
        grade=class_roman,
        year="2025",
        language=language,
        total_marks=total_marks,
        question_count=validation["stats"].get("total_questions", 0),
        section_config={
            s["name"]: {
                "marks": s["marks_per_question"],
                "count": s["question_count"],
                "type": s["type"],
            }
            for s in pattern.get("sections", [])
        },
        config={
            "difficulty": difficulty,
            "pattern_id": pattern_id,
            "generation_model": settings.GENERATION_MODEL,
        },
        formatted_content=raw_content,
        pattern_hash=pattern_hash,
        validation_result=validation,
        created_at=datetime.now(timezone.utc),
    )

    db.add(generated_paper)
    db.commit()
    db.refresh(generated_paper)

    logger.info(
        "Pipeline complete",
        paper_id=str(generated_paper.id),
        valid=validation["valid"],
        total_marks=total_marks,
    )

    return generated_paper
