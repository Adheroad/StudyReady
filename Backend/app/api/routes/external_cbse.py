"""Router for external CBSE website scraping and browsing (legacy integration)."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

# Import legacy logic
# Note: We keep the imports relative to the services directory where they reside
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "services"))

try:
    from utils_cbse import get_all_previous_papers_cbse
    from files import download2client
    from get_paper import process_paper
except ImportError as e:
    # Fallback for different execution contexts
    sys.path.append("/home/adhero/Programming/StudyReady/Backend/services")
    from utils_cbse import get_all_previous_papers_cbse
    from files import download2client
    from get_paper import process_paper

router = APIRouter()

@router.get("/papers", tags=["External CBSE"])
async def list_external_papers(year: Optional[str] = None, grade: Optional[str] = None, subject: Optional[str] = None):
    """Browse papers directly from CBSE website."""
    papers = get_all_previous_papers_cbse()
    if papers is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve papers data")
    
    results = [
        paper for paper in papers
        if paper is not None and (year is None or paper['year'] == year) and
           (grade is None or paper['grade'] == grade) and
           (subject is None or subject.lower() in paper['subject'].lower())
    ]
    return results

@router.get("/papers/{year}/{grade}/{subject}", tags=["External CBSE"])
async def download_external_paper(year: str, grade: str, subject: str):
    """Download a specific paper from CBSE."""
    papers = get_all_previous_papers_cbse()
    if papers is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve papers data")
    
    paper = None
    for p in papers:
        if (p is not None and p['year'] == year and 
            p['grade'] == grade and 
            p['subject'].upper() == subject.upper()):
            paper = p
            break
    
    if not paper:
        raise HTTPException(
            status_code=404, 
            detail=f"Paper not found for {subject} (Grade {grade}, Year {year})"
        )
    
    # download2client normally returns a FileResponse or similar
    return download2client(paper)

@router.get("/papers/{year}/{grade}/{subject}/text", tags=["External CBSE"])
async def get_external_paper_text(year: str, grade: str, subject: str):
    """Extract text from a specific CBSE paper using legacy process."""
    papers = get_all_previous_papers_cbse()
    if papers is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve papers data")
    
    paper = None
    for p in papers:
        if (p is not None and p['year'] == year and 
            p['grade'] == grade and 
            p['subject'].upper() == subject.upper()):
            paper = p
            break
    
    if not paper:
        raise HTTPException(
            status_code=404, 
            detail=f"Paper not found for {subject} (Grade {grade}, Year {year})"
        )
    
    try:
        text = process_paper(paper)
        return {"text": text, "subject": subject, "year": year, "grade": grade}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
