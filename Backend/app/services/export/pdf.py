"""PDF export service for CBSE question papers using WeasyPrint and Jinja2."""

import re
from io import BytesIO
from typing import Optional, List, Dict, Any

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.core.logging import get_logger

logger = get_logger(__name__)



def _parse_markdown_to_data(content: str, subject: str, grade: str, total_marks: int) -> Dict[str, Any]:
    """Parse structured JSON content into Jinja2 template data."""
    import json
    
    # 1. Parse JSON
    try:
        raw = json.loads(content)
    except json.JSONDecodeError:
        # Fallback cleanup just in case
        content = re.sub(r"^```json\s*", "", content.strip(), flags=re.IGNORECASE)
        content = re.sub(r"^```\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content, flags=re.IGNORECASE)
        raw = json.loads(content)

    # 2. Map to Template Context
    data = {
        "subject": subject,
        "grade": grade,
        "total_marks": raw.get("total_marks", total_marks),
        "year": raw.get("year", "2025"),
        "series": raw.get("series", "WXY4Z"),
        "set_num": raw.get("set_num", "4"),
        "qp_code": raw.get("qp_code", "72/1/1"),
        "qp_code_full": raw.get("qp_code", "72/1/1"),
        "set_box": str(1234), # Placeholder or derived
        "subjects_pair": [ # Used for header
             raw.get("subject_hi", "व्यावसायिक कला (सैद्धान्तिक)"),
             raw.get("subject_en", subject)
        ],
        "time": "2",
        "printed_pages": "11",
        "total_questions": sum(len(s.get("questions", [])) for s in raw.get("sections", [])),
        "sections": raw.get("sections", [])
    }

    return data


def generate_pdf(
    paper_content: str,
    subject: str,
    grade: str,
    total_marks: int,
    output_path: Optional[str] = None,
) -> bytes:
    """Generate high-fidelity PDF from markdown content using WeasyPrint."""
    logger.info("Generating high-fidelity PDF", subject=subject, grade=grade)
    
    # Prepare data
    data = _parse_markdown_to_data(paper_content, subject, grade, total_marks)
    
    # Render template
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("paper_pdf.html") 
    html_out = template.render(**data)
    
    # Convert to PDF
    pdf_bytes = HTML(string=html_out).write_pdf()
    
    # Optionally save to file
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        logger.info(f"PDF saved to {output_path}")
        
    return pdf_bytes
