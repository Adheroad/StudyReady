"""Extract questions from PDF using Vision API with configurable page batching."""

import base64
import hashlib
import json
import os
import re
from io import BytesIO

from openai import OpenAI
from pdf2image import convert_from_path
from PIL import Image

from app.config import get_settings
from app.core.logging import get_logger
from app.core.prompts import load_prompt

logger = get_logger(__name__)

# Configurable: Number of pages to process per API call
PAGES_PER_BATCH = int(os.environ.get("EXTRACTION_PAGES_PER_BATCH", "1"))


def _get_client():
    settings = get_settings()
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )


def _image_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """Convert PIL Image to base64 string."""
    buffer = BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _parse_json_response(content: str) -> list[dict]:
    """Parse JSON from LLM response, handling markdown code blocks."""
    content = content.strip()
    # Remove markdown code blocks if present
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "questions" in data:
            return data["questions"]
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON response", extra={"error": str(e)})
        return []


def _crop_and_save_image(
    page_image: Image.Image,
    bounding_box: list,
    pdf_name: str,
    question_number: str,
) -> str | None:
    """Crop image region and save to disk."""
    if not bounding_box or len(bounding_box) != 4:
        return None
    
    try:
        ymin, xmin, ymax, xmax = bounding_box
        width, height = page_image.size
        
        # Convert 0-1000 scale to pixels
        left = int(xmin * width / 1000)
        top = int(ymin * height / 1000)
        right = int(xmax * width / 1000)
        bottom = int(ymax * height / 1000)
        
        cropped = page_image.crop((left, top, right, bottom))
        
        # Generate unique filename
        hash_suffix = hashlib.md5(f"{pdf_name}_{question_number}".encode()).hexdigest()[:6]
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", pdf_name)
        filename = f"{safe_name}_Q{question_number}_{hash_suffix}.png"
        
        os.makedirs("data/images", exist_ok=True)
        filepath = f"data/images/{filename}"
        cropped.save(filepath, "PNG")
        
        logger.debug("Saved cropped image", extra={"path": filepath})
        return filepath
    except Exception as e:
        logger.error("Failed to crop image", extra={"error": str(e)})
        return None


def extract_questions_from_pdf(
    pdf_path: str,
    pages_per_batch: int | None = None,
) -> list[dict]:
    """
    Extract questions from PDF using Vision API.
    
    Args:
        pdf_path: Path to PDF file
        pages_per_batch: Number of pages per API call (default: PAGES_PER_BATCH env var or 1)
    
    Returns:
        List of extracted question dictionaries
    """
    settings = get_settings()
    client = _get_client()
    batch_size = pages_per_batch or PAGES_PER_BATCH
    
    logger.info("Starting extraction", extra={"path": pdf_path, "batch_size": batch_size})
    
    # Load prompt
    extraction_prompt = load_prompt("question_extraction")
    
    # Convert PDF to images
    pages = convert_from_path(pdf_path, dpi=200)
    total_pages = len(pages)
    logger.info(f"Converted PDF to {total_pages} images")
    
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    all_questions = []
    
    # Process pages in batches
    for batch_start in range(0, total_pages, batch_size):
        batch_end = min(batch_start + batch_size, total_pages)
        batch_pages = pages[batch_start:batch_end]
        
        logger.info(f"Processing pages {batch_start + 1}-{batch_end}/{total_pages}")
        
        # Prepare images for API call
        image_content = []
        for page_image in batch_pages:
            img_str = _image_to_base64(page_image)
            image_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_str}"},
            })
        
        # Build message with prompt + images
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": extraction_prompt},
                    *image_content,
                ],
            }
        ]
        
        try:
            response = client.chat.completions.create(
                model=settings.VISION_MODEL,
                messages=messages,
                max_tokens=8000,
                temperature=0.1,
            )
            
            content = response.choices[0].message.content
            batch_questions = _parse_json_response(content)
            
            # Post-process: handle image cropping
            for q in batch_questions:
                if q.get("has_diagram") and q.get("bounding_box"):
                    # Use first page of batch for cropping (approximate)
                    q["image_path"] = _crop_and_save_image(
                        batch_pages[0],
                        q["bounding_box"],
                        pdf_name,
                        q.get("question_number", "unknown"),
                    )
            
            logger.info(f"Extracted {len(batch_questions)} questions from batch")
            all_questions.extend(batch_questions)
            
        except Exception as e:
            logger.error(f"Extraction failed for batch: {e}")
            continue
    
    # Validate and clean results
    validated = _validate_questions(all_questions)
    logger.info(f"Total extracted: {len(validated)} questions")
    
    return validated


def _validate_questions(questions: list[dict]) -> list[dict]:
    """Validate and normalize extracted questions."""
    validated = []
    
    for q in questions:
        if not q.get("question_text"):
            continue
        
        validated.append({
            "question_number": str(q.get("question_number", "")),
            "question_text": q.get("question_text", "").strip(),
            "marks": int(q.get("marks") or 1),
            "section": q.get("section", ""),
            "question_type": q.get("question_type", "short"),
            "chapter": q.get("chapter", ""),
            "topic": q.get("topic", ""),
            "difficulty": q.get("difficulty", "medium"),
            "language": q.get("language", "en"),
            "has_diagram": bool(q.get("has_diagram")),
            "image_path": q.get("image_path"),
            "image_description": q.get("image_description"),
        })
    
    return validated
