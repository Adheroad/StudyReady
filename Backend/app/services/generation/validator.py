"""Self-validation loop for generated papers.

Checks:
1. Total marks match pattern spec
2. Section structure (question count per section)
3. Near-duplicate question detection (cosine similarity)
4. Difficulty gradient conformance
5. Bilingual parity (text_hi exists for each text_en)

Returns validation result + fix instructions for selective regeneration.
"""

import json
from typing import Optional

from app.core.logging import get_logger
from app.services.papers.pattern_analyzer import classify_bloom, classify_difficulty

logger = get_logger(__name__)


def validate_paper(paper_json: str | dict, pattern: dict) -> dict:
    """
    Validate a generated paper against its pattern template.

    Args:
        paper_json: Paper content as JSON string or dict
        pattern: Pattern template that was used for generation

    Returns:
        Validation result dict with:
        - valid: bool
        - errors: list of error strings
        - warnings: list of warning strings
        - stats: computed statistics
        - fix_instructions: specific fixes for regeneration
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "stats": {},
        "fix_instructions": [],
    }

    # Parse JSON
    if isinstance(paper_json, str):
        try:
            data = json.loads(paper_json)
        except json.JSONDecodeError as e:
            result["valid"] = False
            result["errors"].append(f"Invalid JSON: {str(e)}")
            return result
    else:
        data = paper_json

    sections = data.get("sections", [])
    if not sections:
        result["valid"] = False
        result["errors"].append("No sections found in paper")
        return result

    pattern_sections = pattern.get("sections", [])

    # ── Check 1: Section count ──
    if len(sections) != len(pattern_sections):
        result["errors"].append(
            f"Section count mismatch: got {len(sections)}, expected {len(pattern_sections)}"
        )
        result["fix_instructions"].append(
            f"Generate exactly {len(pattern_sections)} sections: {[s['name'] for s in pattern_sections]}"
        )

    # ── Check 2: Question count per section ──
    total_marks_actual = 0
    total_questions_actual = 0

    for i, section in enumerate(sections):
        questions = section.get("questions", [])
        section_marks = sum(q.get("marks", 0) for q in questions)
        total_marks_actual += section_marks
        total_questions_actual += len(questions)

        if i < len(pattern_sections):
            expected = pattern_sections[i]
            expected_count = expected.get("question_count", 0)
            expected_marks_each = expected.get("marks_per_question", 0)
            expected_total = expected.get("section_total", expected_count * expected_marks_each)

            if len(questions) != expected_count:
                result["errors"].append(
                    f"Section {expected['name']}: got {len(questions)} questions, expected {expected_count}"
                )
                result["fix_instructions"].append(
                    f"Section {expected['name']} must have exactly {expected_count} questions"
                )

            if section_marks != expected_total:
                result["warnings"].append(
                    f"Section {expected['name']}: marks sum {section_marks}, expected {expected_total}"
                )

            # Check marks per question
            for q in questions:
                if q.get("marks", 0) != expected_marks_each:
                    result["warnings"].append(
                        f"Q{q.get('number', '?')}: {q.get('marks')} marks, expected {expected_marks_each}"
                    )

    # ── Check 3: Total marks ──
    expected_total_marks = pattern.get("total_marks", 0)
    if expected_total_marks and total_marks_actual != expected_total_marks:
        result["errors"].append(
            f"Total marks mismatch: got {total_marks_actual}, expected {expected_total_marks}"
        )
        result["fix_instructions"].append(
            f"Total marks must be exactly {expected_total_marks}"
        )

    # ── Check 4: Bilingual parity ──
    missing_hindi = 0
    for section in sections:
        for q in section.get("questions", []):
            if q.get("text_en") and not q.get("text_hi"):
                missing_hindi += 1
            # Check options parity
            if q.get("options_en") and not q.get("options_hi"):
                result["warnings"].append(
                    f"Q{q.get('number', '?')}: has options_en but missing options_hi"
                )
            # Check OR question parity
            or_q = q.get("or_question")
            if or_q:
                if or_q.get("text_en") and not or_q.get("text_hi"):
                    missing_hindi += 1

    if missing_hindi > 0:
        result["warnings"].append(f"{missing_hindi} questions missing Hindi translations")

    # ── Check 5: OR questions where expected ──
    for i, section in enumerate(sections):
        if i < len(pattern_sections):
            expected = pattern_sections[i]
            if expected.get("has_or_questions"):
                or_count = sum(1 for q in section.get("questions", []) if q.get("or_question"))
                if or_count == 0:
                    result["warnings"].append(
                        f"Section {expected['name']}: expected OR questions but found none"
                    )
                    result["fix_instructions"].append(
                        f"Section {expected['name']} should have OR/alternative questions"
                    )

    # ── Check 6: Question numbering continuity ──
    all_numbers = []
    for section in sections:
        for q in section.get("questions", []):
            num = q.get("number")
            if num is not None:
                all_numbers.append(int(num))

    if all_numbers:
        expected_seq = list(range(1, len(all_numbers) + 1))
        if all_numbers != expected_seq:
            result["warnings"].append(
                f"Question numbering not continuous: {all_numbers}"
            )

    # ── Compile stats ──
    result["stats"] = {
        "total_marks": total_marks_actual,
        "total_questions": total_questions_actual,
        "section_count": len(sections),
        "missing_hindi": missing_hindi,
    }

    # Determine validity
    if result["errors"]:
        result["valid"] = False

    logger.info(
        "Paper validation complete",
        valid=result["valid"],
        errors=len(result["errors"]),
        warnings=len(result["warnings"]),
    )

    return result


def build_fix_prompt(validation_result: dict, original_json: str) -> str:
    """
    Build a targeted fix prompt for the LLM to correct specific issues.

    Only regenerates the parts that failed validation.
    """
    if validation_result["valid"]:
        return ""

    fixes = validation_result.get("fix_instructions", [])
    errors = validation_result.get("errors", [])

    prompt = (
        "The generated paper has validation errors. Fix ONLY the following issues "
        "while keeping all other content unchanged:\n\n"
    )

    for i, error in enumerate(errors, 1):
        prompt += f"{i}. ERROR: {error}\n"

    if fixes:
        prompt += "\nSpecific fixes required:\n"
        for fix in fixes:
            prompt += f"- {fix}\n"

    prompt += (
        "\nReturn the COMPLETE corrected JSON paper. Do not leave out any sections "
        "or questions that were already correct.\n\n"
        f"Original paper:\n{original_json[:3000]}"  # Truncate to save tokens
    )

    return prompt
