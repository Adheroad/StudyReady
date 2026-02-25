"""NCERT textbook scraper — dynamic discovery via Playwright (Async version).

Navigates ncert.nic.in/textbook.php and interacts with the three JS-driven
dropdowns (tclass → tsubject → tbook) to dynamically discover all available
subjects, books, and chapter PDF URLs for Class X and XII.

Uses async_playwright to avoid conflicts with FastAPI's asyncio loop.
"""

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from app.core.logging import get_logger

logger = get_logger(__name__)

BASE_URL = "https://ncert.nic.in/textbook.php"
PDF_BASE = "https://ncert.nic.in/textbook/pdf/"
ALLOWED_DOMAIN = "ncert.nic.in"

# Only scrape these classes
TARGET_CLASSES = {"10", "12"}


@dataclass
class NCERTBook:
    """Represents a single discovered NCERT textbook."""
    book_code: str
    title: str
    subject: str
    target_class: str
    total_chapters: int
    book_url: str  # e.g. textbook.php?jesc1=0-13


@dataclass
class ChapterPDF:
    """Represents a single downloadable chapter PDF."""
    book_code: str
    chapter_num: int
    pdf_url: str
    subject: str
    book_title: str
    target_class: str


def _is_valid_ncert_url(url: str) -> bool:
    """Validate URL is from ncert.nic.in domain only."""
    parsed = urlparse(url)
    return parsed.netloc in (ALLOWED_DOMAIN, f"www.{ALLOWED_DOMAIN}")


async def fetch_catalog(
    target_class_filter: str | None = None,
    subject_filter: str | None = None,
) -> list[NCERTBook]:
    """
    Dynamically discover all NCERT textbooks for target classes by
    interacting with the dropdown menus on ncert.nic.in/textbook.php.
    Allows filtering by class and subject to minimize scraping time.

    Returns:
        List of NCERTBook objects with book codes and chapter counts.
    """
    logger.info(
        "Fetching NCERT catalog via Playwright (Async)",
        url=BASE_URL,
        target_class=target_class_filter,
        subject=subject_filter,
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            # "domcontentloaded" is safer than "networkidle" for slow, ad-heavy, or analytic-heavy sites like NCERT.
            await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)

            all_books: list[NCERTBook] = []

            classes_to_scan = TARGET_CLASSES
            if target_class_filter:
                classes_to_scan = [target_class_filter] if target_class_filter in TARGET_CLASSES else []

            # Step 1: Iterate through target classes
            for target_class in classes_to_scan:
                logger.info("Discovering subjects for class", target_class=target_class)

                # Select the class in the dropdown
                await page.select_option('select[name="tclass"]', target_class)
                # Trigger the JS change() function
                await page.evaluate('document.querySelector(\'select[name="tclass"]\').dispatchEvent(new Event("change"))')
                await page.wait_for_timeout(500)

                # Step 2: Read all subject options
                subjects = await page.evaluate('''() => {
                    const sel = document.querySelector('select[name="tsubject"]');
                    if (!sel) return [];
                    return Array.from(sel.options)
                        .filter(o => o.value && o.value !== "0")
                        .map(o => ({value: o.value, text: o.text.trim()}));
                }''')

                if not subjects:
                    logger.warning("No subjects found for class", target_class=target_class)
                    continue

                logger.info("Subjects discovered", target_class=target_class, count=len(subjects))

                # Step 3: For each subject, get available books
                for subj in subjects:
                    if subject_filter and subj["text"].lower() != subject_filter.lower():
                        continue

                    await page.select_option('select[name="tsubject"]', subj["value"])
                    await page.evaluate('document.querySelector(\'select[name="tsubject"]\').dispatchEvent(new Event("change"))')
                    await page.wait_for_timeout(500)

                    books = await page.evaluate('''() => {
                        const sel = document.querySelector('select[name="tbook"]');
                        if (!sel) return [];
                        return Array.from(sel.options)
                            .filter(o => o.value && o.value !== "0")
                        .map(o => ({value: o.value, text: o.text.trim()}));
                    }''')

                    if not books:
                        logger.debug("No books for subject", subject=subj["text"])
                        continue

                    for book_opt in books:
                        # Book value is the URL: textbook.php?jesc1=0-13
                        book_url = book_opt["value"]
                        book_title = book_opt["text"]

                        # Parse book code and chapter count from URL
                        # Pattern: textbook.php?<code>=<start>-<total>
                        match = re.search(r'\?(\w+)=(\d+)-(\d+)', book_url)
                        if not match:
                            logger.debug("Could not parse book URL", url=book_url)
                            continue

                        book_code = match.group(1)
                        total_chapters = int(match.group(3))

                        ncert_book = NCERTBook(
                            book_code=book_code,
                            title=book_title,
                            subject=subj["text"],
                            target_class=target_class,
                            total_chapters=total_chapters,
                            book_url=book_url,
                        )
                        all_books.append(ncert_book)
                        logger.debug(
                            "Book discovered",
                            code=book_code,
                            title=book_title,
                            chapters=total_chapters,
                        )

            logger.info("NCERT catalog fetched", total_books=len(all_books))
            return all_books

        finally:
            await browser.close()


async def list_subjects(target_class: str) -> list[dict]:
    """
    List all available subjects for a class by querying the live site.
    """
    all_books = await fetch_catalog()

    # Filter by class
    class_books = [b for b in all_books if b.target_class == target_class]

    # Group by subject
    subjects: dict[str, list] = {}
    for book in class_books:
        if book.subject not in subjects:
            subjects[book.subject] = []
        subjects[book.subject].append(book)

    return [
        {
            "name": subj,
            "books": len(book_list),
            "book_titles": [b.title for b in book_list],
        }
        for subj, book_list in sorted(subjects.items())
    ]


async def list_books(target_class: str, subject: Optional[str] = None) -> list[dict]:
    """
    List books for a class, optionally filtered by subject.
    """
    all_books = await fetch_catalog()

    filtered = [b for b in all_books if b.target_class == target_class]
    if subject:
        subject_lower = subject.lower()
        filtered = [b for b in filtered if b.subject.lower() == subject_lower]

    return [
        {
            "code": b.book_code,
            "title": b.title,
            "subject": b.subject,
            "total_chapters": b.total_chapters,
            "book_url": b.book_url,
        }
        for b in filtered
    ]


def get_chapter_pdfs(book: NCERTBook) -> list[ChapterPDF]:
    """
    Generate chapter PDF URLs for a discovered book.
    """
    pdfs = []
    for ch_num in range(1, book.total_chapters + 1):
        pdf_url = f"{PDF_BASE}{book.book_code}{ch_num:02d}.pdf"
        pdfs.append(ChapterPDF(
            book_code=book.book_code,
            chapter_num=ch_num,
            pdf_url=pdf_url,
            subject=book.subject,
            book_title=book.title,
            target_class=book.target_class,
        ))
    return pdfs


async def discover_pdfs_for_subject(
    target_class: str,
    subject: str,
) -> list[ChapterPDF]:
    """
    Discover all chapter PDFs for a subject by querying the live site.
    """
    all_books = await fetch_catalog(target_class_filter=target_class, subject_filter=subject)

    subject_lower = subject.lower()
    matching = [
        b for b in all_books
        if b.target_class == target_class and b.subject.lower() == subject_lower
    ]

    if not matching:
        logger.warning("No books found", target_class=target_class, subject=subject)
        return []

    all_pdfs: list[ChapterPDF] = []
    for book in matching:
        all_pdfs.extend(get_chapter_pdfs(book))

    logger.info(
        "PDFs discovered for subject",
        target_class=target_class,
        subject=subject,
        books=len(matching),
        total_pdfs=len(all_pdfs),
    )
    return all_pdfs
