"""NCERT PDF downloader with integrity checks and idempotent storage."""

import hashlib
import os
import re
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Constraints
MIN_FILE_SIZE = 50 * 1024       # 50 KB
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
CHUNK_SIZE = 8192
REQUEST_DELAY = 1.0


def _get_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "StudyReady/1.0 (Educational Tool)"})
    return session


def _slug(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text


def compute_checksum(data: bytes) -> str:
    """Compute SHA256 checksum of bytes."""
    return hashlib.sha256(data).hexdigest()


def download_pdf(
    pdf_url: str,
    target_class: str,
    subject: str,
    session: requests.Session | None = None,
) -> dict | None:
    """
    Download a single PDF with validation.

    Returns dict with file_path, checksum, file_size, or None on failure.
    """
    if session is None:
        session = _get_session()

    logger.info("Downloading PDF", url=pdf_url)
    time.sleep(REQUEST_DELAY)

    try:
        resp = session.get(pdf_url, timeout=30, stream=True)
        resp.raise_for_status()

        # Validate Content-Type
        content_type = resp.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and "octet-stream" not in content_type.lower():
            logger.warning("Invalid Content-Type", url=pdf_url, content_type=content_type)
            return None

        # Stream download
        chunks = []
        total_size = 0
        for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
            chunks.append(chunk)
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                logger.warning("File too large, aborting", url=pdf_url, size=total_size)
                return None

        data = b"".join(chunks)

        if len(data) < MIN_FILE_SIZE:
            logger.warning("File too small", url=pdf_url, size=len(data))
            return None

        # Compute checksum
        checksum = compute_checksum(data)

        # Build deterministic path
        subject_slug = _slug(subject)
        data_dir = Path(settings.DATA_DIR)
        target_dir = data_dir / "raw" / "ncert" / f"class_{target_class}" / subject_slug
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / f"{checksum}.pdf"

        # Write file (idempotent — same hash = same file)
        if not file_path.exists():
            with open(file_path, "wb") as f:
                f.write(data)
            logger.info("PDF saved", path=str(file_path), size=len(data))
        else:
            logger.info("PDF already exists (same checksum)", path=str(file_path))

        return {
            "file_path": str(file_path),
            "checksum": checksum,
            "file_size": len(data),
        }

    except requests.RequestException as e:
        logger.error("Download failed", url=pdf_url, error=str(e))
        return None


def download_subject_pdfs(
    target_class: str,
    subject: str,
    pdf_urls: list[dict],
) -> list[dict]:
    """
    Download all PDFs for a subject.

    Args:
        target_class: "10" or "12"
        subject: Subject name
        pdf_urls: List of dicts with at least "pdf_url" key

    Returns:
        List of download result dicts.
    """
    session = _get_session()
    results = []

    for pdf_info in pdf_urls:
        url = pdf_info.get("pdf_url") or pdf_info.get("url")
        if not url:
            continue

        result = download_pdf(url, target_class, subject, session)
        if result:
            result["source_url"] = url
            result["book_title"] = pdf_info.get("book_title", "")
            result["chapter"] = pdf_info.get("chapter_title", "")
            results.append(result)

    logger.info(
        "Batch download complete",
        target_class=target_class,
        subject=subject,
        downloaded=len(results),
        total=len(pdf_urls),
    )
    return results
