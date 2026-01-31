"""CBSE paper scraper - fetches paper metadata from CBSE website."""

from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.core.logging import get_logger

logger = get_logger(__name__)

BASE_URL = "https://www.cbse.gov.in/cbsenew/"
PAPERS_URL = f"{BASE_URL}question-paper.html"


def fetch_all_papers() -> list[dict]:
    """
    Fetch all available CBSE papers from the official website.

    Returns:
        List of paper dicts with subject, grade, year, link, size
    """
    logger.info("Fetching papers from CBSE website", url=PAPERS_URL)

    try:
        response = requests.get(PAPERS_URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to fetch CBSE papers", error=str(e))
        raise

    papers = _parse_papers_html(response.content)
    logger.info("Fetched papers successfully", count=len(papers))

    return papers


def get_papers_by_subject(
    subject: str,
    grade: Optional[str] = None,
    year: Optional[str] = None,
) -> list[dict]:
    """
    Filter papers by subject name (case-insensitive partial match).

    Args:
        subject: Subject name to filter (e.g., "commercial art", "design")
        grade: Optional grade filter (e.g., "XII", "X")
        year: Optional year filter (e.g., "2024", "2023")

    Returns:
        Filtered list of papers
    """
    all_papers = fetch_all_papers()

    filtered = [
        p
        for p in all_papers
        if p and subject.lower() in p.get("subject", "").lower()
    ]

    if grade:
        filtered = [p for p in filtered if p.get("grade") == grade]

    if year:
        filtered = [p for p in filtered if p.get("year") == year]

    logger.info(
        "Filtered papers",
        subject=subject,
        grade=grade,
        year=year,
        count=len(filtered),
    )

    return filtered


def _parse_papers_html(html_content: bytes) -> list[dict]:
    """Parse CBSE papers HTML and extract paper details."""
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")

    papers = []
    for table in tables:
        for row in table.find_all("tr"):
            paper = _parse_paper_row(row)
            if paper:
                papers.append(paper)

    return papers


def _parse_paper_row(row) -> Optional[dict]:
    """Parse a single table row into paper dict."""
    cells = row.find_all("td")
    if len(cells) < 3:
        return None

    try:
        # Find link in any cell
        link_elem = None
        for cell in cells:
            link_elem = cell.find("a")
            if link_elem:
                break

        if not link_elem:
            return None

        href = link_elem.get("href", "")
        if not href or not (href.endswith(".pdf") or href.endswith(".zip")):
            return None

        url = urljoin(BASE_URL, href)

        # Extract subject from first cell or link text
        subject = cells[0].get_text(strip=True) or link_elem.get_text(strip=True)

        # Try to extract year and grade from URL path
        parts = href.split("/")
        year = ""
        grade = ""

        for part in parts:
            if part.isdigit() and len(part) == 4:
                year = part
            elif part.upper() in ("X", "XII", "IX", "XI"):
                grade = part.upper()

        # Get size if available
        size = ""
        if len(cells) > 2:
            size = cells[-1].get_text(strip=True)

        return {
            "subject": subject,
            "year": year,
            "grade": grade,
            "size": size,
            "link": url,
        }
    except (IndexError, AttributeError) as e:
        logger.debug("Failed to parse paper row", error=str(e))
        return None
