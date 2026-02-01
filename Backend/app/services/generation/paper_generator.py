"""Paper generation service using LLM for CBSE formatting."""

import json
from typing import Optional

from openai import OpenAI

from app.config import get_settings
from app.core.logging import get_logger
from app.core.prompts import load_prompt
from app.database.models import Question

logger = get_logger(__name__)


def _get_client():
    settings = get_settings()
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )


def _prepare_questions_json(questions: list[Question]) -> str:
    """Convert Question objects to JSON for LLM prompt."""
    questions_data = []
    
    for q in questions:
        # Minimal data to save tokens
        questions_data.append({
            "text": q.question_text,
            "marks": q.marks
        })
    
    return json.dumps(questions_data, ensure_ascii=False)


def generate_formatted_paper(
    questions: list[Question],
    subject: str,
    grade: str,
    total_marks: int,
    language: str = "en",
) -> str:
    """
    Generate a formatted CBSE paper from selected questions.
    
    Args:
        questions: List of selected Question objects
        subject: Subject name (e.g., "Commercial Art")
        grade: Grade level (e.g., "XII")
        total_marks: Total marks for the paper
        language: Paper language ("en", "hi", or "both")
    
    Returns:
        Formatted paper content as markdown string
    """
    settings = get_settings()
    client = _get_client()
    
    logger.info(
        "Generating formatted paper",
        subject=subject,
        grade=grade,
        total_marks=total_marks,
        question_count=len(questions),
        language=language,
    )
    
    # Load formatting prompt template
    prompt_template = load_prompt("paper_formatting")
    
    # Prepare questions JSON
    questions_json = _prepare_questions_json(questions)
    
    # Fill template
    prompt = prompt_template.format(
        subject=subject,
        grade=grade,
        total_marks=total_marks,
        language=language,
        questions_json=questions_json,
    )
    
    try:
        response = client.chat.completions.create(
            model=settings.GENERATION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert CBSE question paper formatter. Return only the formatted paper content as a valid JSON object. No explanations, no markdown blocks.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3, # Lower temperature for better JSON adherence
            max_tokens=1500,
            response_format={ "type": "json_object" }
        )
        
        content = response.choices[0].message.content.strip()
        
        # Validate and Repair JSON
        try:
            # First pass: Standard parse
            json.loads(content)
        except json.JSONDecodeError as jde:
            logger.warning("Initial JSON parsing failed, attempting repair", error=str(jde))
            
            # Step 1: Remove markdown wrappers
            cleaned = content.replace("```json", "").replace("```", "").strip()
            
            # Step 2: Handle truncated JSON (common with long papers)
            if not cleaned.endswith("}"):
                logger.warning("JSON appears truncated, attempting to close blocks")
                # Basic balance (very naive but can help)
                open_braces = cleaned.count("{")
                close_braces = cleaned.count("}")
                if open_braces > close_braces:
                    cleaned += "}" * (open_braces - close_braces)

            try:
                json.loads(cleaned)
                content = cleaned
            except json.JSONDecodeError as jde2:
                # Last resort: Try a very aggressive repair or return raw
                logger.error("JSON repair failed completely. Saving raw response for recovery.", content_preview=content[:200])
                # We return the content anyway but log it, so it can be manually fixed in DB if needed
                # instead of raising and wasting tokens
                return content 
            
        logger.info("Paper formatting complete (JSON Validated/Recovered)")
        return content
        
    except Exception as e:
        logger.error("Paper formatting failed", error=str(e))
        raise


def validate_paper_structure(paper_content: str) -> dict:
    """
    Validate the generated paper structure.
    
    Returns:
        Dict with validation results and warnings
    """
    validation = {
        "valid": True,
        "warnings": [],
        "stats": {},
    }
    
    # Check for required sections
    required_sections = ["CENTRAL BOARD", "GENERAL INSTRUCTIONS", "SECTION"]
    for section in required_sections:
        if section not in paper_content:
            validation["warnings"].append(f"Missing: {section}")
            validation["valid"] = False
    
    # Count questions
    question_count = paper_content.count("\n1.") + paper_content.count("\n2.")
    validation["stats"]["estimated_questions"] = question_count
    
    # Check for OR questions
    or_count = paper_content.count(" OR ")
    validation["stats"]["or_questions"] = or_count
    
    logger.debug("Paper validation", extra=validation)
    
    return validation
