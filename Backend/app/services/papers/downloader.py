"""Paper downloader - downloads PDF files from CBSE."""

import zipfile
from pathlib import Path

import requests

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def download_paper(paper: dict) -> str:
    """
    Download paper PDF to local storage.

    Args:
        paper: Paper dict with 'link', 'subject', 'year' keys

    Returns:
        Path to downloaded file
    """
    settings = get_settings()
    papers_dir = Path(settings.DATA_DIR) / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    subject_clean = paper.get("subject", "unknown").replace(" ", "_").replace("/", "-")
    year = paper.get("year", "unknown")
    grade = paper.get("grade", "XII")

    url = paper["link"]
    ext = ".zip" if url.endswith(".zip") else ".pdf"
    filename = f"{year}_{grade}_{subject_clean}{ext}"
    filepath = papers_dir / filename

    # Check if already downloaded
    if filepath.exists():
        logger.debug("Paper already downloaded", path=str(filepath))
        # Still need to extract if it's a ZIP
        if ext == ".zip":
            return _extract_zip(filepath)
        return str(filepath)

    # Download
    logger.info("Downloading paper", url=url, filename=filename)

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info("Downloaded paper", path=str(filepath), size=filepath.stat().st_size)

        # Extract if ZIP
        if ext == ".zip":
            pdf_path = _extract_zip(filepath)
            return pdf_path

        return str(filepath)

    except requests.RequestException as e:
        logger.error("Failed to download paper", url=url, error=str(e))
        raise


def _extract_zip(zip_path: Path) -> str:
    """
    Extract ZIP file and return path to PDF inside.

    Args:
        zip_path: Path to ZIP file

    Returns:
        Path to extracted PDF
    """
    extract_dir = zip_path.parent / zip_path.stem
    extract_dir.mkdir(exist_ok=True)

    logger.debug("Extracting ZIP", path=str(zip_path))

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    # Find PDF files
    pdf_files = list(extract_dir.glob("**/*.pdf"))

    if not pdf_files:
        logger.error("No PDF found in ZIP", zip_path=str(zip_path))
        raise ValueError(f"No PDF found in {zip_path}")

    if len(pdf_files) == 1:
        return str(pdf_files[0])

    # If multiple PDFs, merge them or return first
    logger.warning(
        "Multiple PDFs in ZIP, using first",
        count=len(pdf_files),
        selected=str(pdf_files[0]),
    )
    return str(pdf_files[0])


def get_downloaded_papers() -> list[str]:
    """Get list of already downloaded paper paths."""
    settings = get_settings()
    papers_dir = Path(settings.DATA_DIR) / "papers"

    if not papers_dir.exists():
        return []

    return [str(p) for p in papers_dir.glob("*.pdf")]
