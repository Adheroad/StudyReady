"""NCERT PDF processor — text extraction, chunking, and embedding."""

from pathlib import Path
from typing import Any

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.models import NCERTContent, IngestionRegistry
from app.services.embeddings.gemini_embeddings import (
    generate_embeddings_batch,
    EmbeddingError,
)

logger = get_logger(__name__)


def extract_text_from_pdf(file_path: str) -> tuple[str, list[dict]]:
    """
    Extract text from a PDF file, page by page.

    Returns:
        Tuple of (full_text, page_metadata).
    """
    reader = PdfReader(file_path)
    full_text = ""
    page_metadata = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            page_metadata.append({"page": i + 1, "char_start": len(full_text)})
            full_text += text + "\n"

    return full_text, page_metadata


def chunk_text(
    full_text: str,
    page_metadata: list[dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """
    Split text into overlapping chunks with page provenance.

    Returns:
        List of dicts with 'content' and 'metadata' keys.
    """
    chunks = []
    start = 0

    while start < len(full_text):
        end = min(start + chunk_size, len(full_text))
        chunk_text_content = full_text[start:end]

        # Skip chunks that are mostly whitespace
        if not chunk_text_content.strip() or len(chunk_text_content.strip()) < 50:
            start += chunk_size - chunk_overlap
            if start >= len(full_text):
                break
            continue

        # Find which page this chunk belongs to
        chunk_page = 1
        for meta in reversed(page_metadata):
            if start >= meta["char_start"]:
                chunk_page = meta["page"]
                break

        chunks.append({
            "content": chunk_text_content,
            "metadata": {"page": chunk_page},
        })

        if end >= len(full_text):
            break
        start += chunk_size - chunk_overlap

    return chunks


def process_ncert_pdf(
    db: Session,
    registry_id: Any,
    file_path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> int:
    """
    Process a single NCERT PDF:
    1. Extract text page by page
    2. Split into overlapping chunks
    3. Generate embeddings in batches
    4. Store in NCERTContent table
    5. Update registry status to 'embedded'

    Returns:
        Number of chunks successfully embedded.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error("PDF file not found", path=file_path)
        _update_registry_status(db, registry_id, "failed")
        return 0

    logger.info("Processing NCERT PDF", path=file_path, registry_id=str(registry_id))

    try:
        # 1. Extract text
        full_text, page_metadata = extract_text_from_pdf(file_path)

        if not full_text.strip():
            logger.warning("No text extracted from PDF (may be scanned/image-based)", path=file_path)
            _update_registry_status(db, registry_id, "failed_no_text")
            return 0

        # 2. Chunk
        chunks = chunk_text(full_text, page_metadata, chunk_size, chunk_overlap)
        logger.info("Generated chunks", count=len(chunks), path=file_path)

        if not chunks:
            logger.warning("No valid chunks after filtering", path=file_path)
            _update_registry_status(db, registry_id, "failed_no_text")
            return 0

        # 3. Generate embeddings in batch
        chunk_texts = [c["content"] for c in chunks]
        try:
            embeddings = generate_embeddings_batch(chunk_texts)
        except EmbeddingError as e:
            logger.error("Embedding batch failed", path=file_path, error=str(e))
            _update_registry_status(db, registry_id, "failed_embedding")
            return 0

        # 4. Store chunks — skip any with None embeddings
        stored_count = 0
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding is None:
                logger.warning("Skipping chunk with failed embedding", chunk_index=i)
                continue

            content_entry = NCERTContent(
                registry_id=registry_id,
                chunk_index=i,
                content=chunk["content"],
                embedding=embedding,
                chunk_metadata=chunk["metadata"],
            )
            db.add(content_entry)
            stored_count += 1

        # 5. Update registry status
        if stored_count == 0:
            _update_registry_status(db, registry_id, "failed_embedding")
            db.commit()
            return 0

        _update_registry_status(db, registry_id, "embedded")
        db.commit()

        logger.info(
            "PDF fully embedded",
            path=file_path,
            total_chunks=len(chunks),
            stored_chunks=stored_count,
            skipped=len(chunks) - stored_count,
        )
        return stored_count

    except Exception as e:
        db.rollback()
        logger.error("Failed to process NCERT PDF", path=file_path, error=str(e))
        _update_registry_status(db, registry_id, "failed")
        try:
            db.commit()
        except Exception:
            pass
        return 0


def _update_registry_status(db: Session, registry_id: Any, status: str):
    """Update the ingestion registry status."""
    registry = db.get(IngestionRegistry, registry_id)
    if registry:
        registry.status = status
