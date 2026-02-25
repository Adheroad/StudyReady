"""NCERT Textbook API routes — dynamically browse and trigger ingestion."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.connection import get_db
from app.services.ncert.scraper import (
    list_subjects,
    list_books,
    fetch_catalog,
    TARGET_CLASSES,
)
from app.services.ncert.ingestion import ingest_subject

logger = get_logger(__name__)

router = APIRouter()


@router.get("/classes")
async def get_classes():
    """List supported NCERT classes."""
    return {"classes": sorted(TARGET_CLASSES)}


@router.get("/subjects")
async def get_subjects(target_class: str):
    """
    List subjects available for a class.
    Dynamically scraped from ncert.nic.in.
    """
    if target_class not in TARGET_CLASSES:
        raise HTTPException(
            status_code=404,
            detail=f"Class {target_class} not supported. Use: {', '.join(sorted(TARGET_CLASSES))}",
        )

    try:
        subjects = await list_subjects(target_class)
    except Exception as e:
        logger.error("Failed to fetch subjects", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to scrape NCERT: {e}")

    return {
        "class": target_class,
        "subjects": subjects,
    }


@router.get("/books")
async def get_books(target_class: str, subject: str | None = None):
    """
    List books for a class, optionally filtered by subject.
    Dynamically scraped from ncert.nic.in.
    """
    if target_class not in TARGET_CLASSES:
        raise HTTPException(
            status_code=404,
            detail=f"Class {target_class} not supported.",
        )

    try:
        books = await list_books(target_class, subject)
    except Exception as e:
        logger.error("Failed to fetch books", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to scrape NCERT: {e}")

    return {
        "class": target_class,
        "subject": subject,
        "books": books,
    }


@router.post("/ingest")
async def trigger_ingestion(
    target_class: str,
    subject: str,
    reprocess: bool = False,
    db: Session = Depends(get_db),
):
    """
    Trigger NCERT textbook ingestion for a class + subject.

    Dynamically discovers PDFs from ncert.nic.in (Async), downloads new/changed ones,
    and registers them in the ingestion_registry table.
    """
    if target_class not in TARGET_CLASSES:
        raise HTTPException(
            status_code=404,
            detail=f"Class {target_class} not supported.",
        )

    logger.info("NCERT ingestion triggered", target_class=target_class, subject=subject)

    try:
        summary = await ingest_subject(db, target_class, subject, reprocess=reprocess)
    except Exception as e:
        logger.error("Ingestion failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    return {
        "status": "completed",
        "class": target_class,
        "subject": subject,
        "summary": summary,
    }


@router.get("/status")
async def ingestion_status(
    target_class: str | None = None,
    db: Session = Depends(get_db),
):
    """Get ingestion status summary from the registry."""
    from app.database.models import IngestionRegistry
    from sqlalchemy import func

    query = db.query(
        IngestionRegistry.target_class,
        IngestionRegistry.subject,
        IngestionRegistry.status,
        func.count(IngestionRegistry.id).label("count"),
    ).group_by(
        IngestionRegistry.target_class,
        IngestionRegistry.subject,
        IngestionRegistry.status,
    )

    if target_class:
        query = query.filter(IngestionRegistry.target_class == target_class)

    rows = query.all()

    results = {}
    for row in rows:
        key = f"class_{row.target_class}_{row.subject}"
        if key not in results:
            results[key] = {
                "class": row.target_class,
                "subject": row.subject,
                "downloaded": 0,
                "embedded": 0,
                "failed": 0,
            }
        results[key][row.status] = row.count

    return {"registry": list(results.values())}


@router.get("/embedded_books")
async def get_embedded_books(
    target_class: str | None = None,
    subject: str | None = None,
    db: Session = Depends(get_db),
):
    """List all books that have been successfully embedded and are ready for RAG."""
    from app.database.models import IngestionRegistry
    import json
    from pathlib import Path
    from app.config import get_settings

    settings = get_settings()
    metadata_dir = Path(settings.DATA_DIR) / "metadata" / "ncert"

    query = db.query(IngestionRegistry).filter(IngestionRegistry.status == "embedded")

    if target_class:
        query = query.filter(IngestionRegistry.target_class == target_class)
    if subject:
        query = query.filter(IngestionRegistry.subject == subject)

    embedded_entries = query.all()

    # The DB registry only stores source_url, hash, class, subject.
    # To get the book_title and chapter_num, we read the metadata JSONs we saved during ingestion.
    results = []
    
    # Group by book title by reading metadata.
    # Since we need book-level visibility, we will group chapters into books.
    books_map = {}

    for entry in embedded_entries:
        meta_path = metadata_dir / f"{entry.file_hash}.json"
        
        book_title = "Unknown Book"
        chapter_num = "Unknown"
        
        if meta_path.exists():
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    book_title = meta.get("book_title", book_title)
                    chapter_num = meta.get("chapter_num", chapter_num)
            except Exception:
                pass
                
        key = f"{entry.target_class}_{entry.subject}_{book_title}"
        
        if key not in books_map:
            books_map[key] = {
                "class": entry.target_class,
                "subject": entry.subject,
                "book_title": book_title,
                "embedded_chapters": [],
            }
            
        books_map[key]["embedded_chapters"].append({
            "chapter_num": chapter_num,
            "registry_id": str(entry.id),
            "updated_at": entry.last_processed_at.isoformat() if entry.last_processed_at else None
        })

    # Sort chapters numerically if possible
    for b in books_map.values():
        b["embedded_chapters"].sort(
            key=lambda x: int(x["chapter_num"]) if str(x["chapter_num"]).isdigit() else 999
        )

    return {"books": list(books_map.values())}
