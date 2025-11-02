from fastapi import FastAPI, HTTPException
from utils_cbse import get_all_previous_papers_cbse
from files import download2client
from get_paper import process_paper


app = FastAPI()

# API to load all papers dynamically
@app.get("/dynamic_papers", tags=["Dynamic Paper"])
async def root(year: str = None, grade: str = None, subject: str = None):
    papers = get_all_previous_papers_cbse()
    if papers is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve papers data")
    results = [
        paper for paper in papers
        if paper is not None and (year is None or paper['year'] == year) and
           (grade is None or paper['grade'] == grade) and
           (subject is None or paper['subject'].lower() == subject.lower())
    ]
    return results


# Api to load paper by years
@app.get("/papers/{year}", tags=["Papers by Filters"])
async def list_by_year(year: str):
    papers = get_all_previous_papers_cbse()
    if papers is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve papers data")
    
    results = [p for p in papers if p is not None and p['year'] == year]
    return results

# Api to load paper by years and grade
@app.get("/papers/{year}/{grade}", tags=["Papers by Filters"])
async def list_by_year_grade(year: str, grade: str):
    papers = get_all_previous_papers_cbse()
    if papers is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve papers data")
    
    results = [p for p in papers if  p is not None and p['year'] == year and p['grade'] == grade]
    return results

# Api to load paper by years and grade
@app.get("/papers/{year}/{grade}/{subject}", tags=["Papers by Filters"])
async def get_paper(year: str, grade: str, subject: str):
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
    
    return download2client(paper)

@app.get("/papers/{year}/{grade}/{subject}/text")
async def get_paper_text(year: str, grade: str, subject: str):
    papers = get_all_previous_papers_cbse()
    print("getting papers data")
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
        print("Printing paper results")
        text = process_paper(paper)
        return {"text": text, "subject": subject, "year": year, "grade": grade}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))