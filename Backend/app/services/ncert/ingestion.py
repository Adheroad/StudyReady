"""NCERT ingestion service — orchestrates scraping, downloading, and embedding."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.logging import get_logger
from app.database.models import IngestionRegistry
from app.services.ncert.scraper import discover_pdfs_for_subject, list_subjects, list_books
from app.services.ncert.downloader import download_pdf, compute_checksum
from app.services.ncert.processor import process_ncert_pdf

logger = get_logger(__name__)
settings = get_settings()


async def ingest_subject(
    db: Session,
    target_class: str,
    subject: str,
    reprocess: bool = False,
) -> dict:
    """
    Full ingestion pipeline for a subject (Async):
    1. Discover PDFs via async scraper
    2. Download new/changed PDFs
    3. Update ingestion registry
    """
    logger.info("Starting NCERT ingestion", target_class=target_class, subject=subject, reprocess=reprocess)

    # Step 1: Discover chapter PDFs (Async call)
    discovered = await discover_pdfs_for_subject(target_class, subject)

    if not discovered:
        logger.warning("No PDFs discovered", target_class=target_class, subject=subject)
        return {
            "status": "completed",
            "pdfs_discovered": 0,
            "new_ingested": 0,
            "duplicates_skipped": 0,
            "failures": [],
        }

    new_ingested = 0
    duplicates_skipped = 0
    failures = []

    for pdf_info in discovered:
        source_url = pdf_info.pdf_url

        try:
            # Check registry
            existing = db.query(IngestionRegistry).filter_by(source_url=source_url).first()

            if existing and existing.status == "embedded" and not reprocess:
                duplicates_skipped += 1
                logger.debug("Skipping already-embedded URL", url=source_url)
                continue

            # Download
            result = download_pdf(source_url, target_class, subject)

            if not result:
                failures.append({"url": source_url, "error": "download_failed"})
                continue

            # Check if checksum changed
            if existing and existing.file_hash == result["checksum"] and not reprocess:
                duplicates_skipped += 1
                continue

            # Save metadata JSON
            metadata_dir = Path(settings.DATA_DIR) / "metadata" / "ncert"
            metadata_dir.mkdir(parents=True, exist_ok=True)
            metadata = {
                "class": target_class,
                "subject": subject,
                "book_title": pdf_info.book_title,
                "chapter_num": pdf_info.chapter_num,
                "source_url": source_url,
                "crawl_timestamp": datetime.now(timezone.utc).isoformat(),
                "checksum": result["checksum"],
                "file_size": result["file_size"],
            }
            meta_path = metadata_dir / f"{result['checksum']}.json"
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=2)

            # Upsert registry
            if existing:
                existing.file_hash = result["checksum"]
                existing.status = "downloaded"
                existing.last_processed_at = datetime.now(timezone.utc)
            else:
                registry_entry = IngestionRegistry(
                    id=uuid.uuid4(),
                    source_url=source_url,
                    file_hash=result["checksum"],
                    target_class=target_class,
                    subject=subject,
                    status="downloaded",
                    last_processed_at=datetime.now(timezone.utc),
                )
                db.add(registry_entry)

            db.commit()
            
            # Step 4: Process for RAG (Chunking & Embedding)
            # This is synchronous but called within the ingestion loop
            # Path: data/raw/ncert/class_10/subject/checksum.pdf
            local_path = result["file_path"]
            registry_id = existing.id if existing else registry_entry.id
            
            logger.info("Triggering PDF processing", url=source_url)
            process_ncert_pdf(db, registry_id, local_path)
            
            new_ingested += 1

        except Exception as e:
            db.rollback()
            logger.error("Ingestion error", url=source_url, error=str(e))
            failures.append({"url": source_url, "error": str(e)})

    summary = {
        "status": "completed",
        "pdfs_discovered": len(discovered),
        "new_ingested": new_ingested,
        "duplicates_skipped": duplicates_skipped,
        "failures": failures,
    }
    logger.info("NCERT ingestion complete", **summary)
    return summary
