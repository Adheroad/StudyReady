#!/usr/bin/env python3
"""Clean up orphaned images from data/images that are not referenced in the database."""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def cleanup_orphaned_images(dry_run: bool = True):
    """
    Remove images from data/images that are not referenced in the database.
    
    Args:
        dry_run: If True, only report what would be deleted without actually deleting
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    # Get all image paths from database
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT DISTINCT image_path FROM questions WHERE image_path IS NOT NULL")
        )
        db_images = {row[0] for row in result}
    
    logger.info(f"Found {len(db_images)} images referenced in database")
    
    # Get all image files from disk
    images_dir = Path("data/images")
    if not images_dir.exists():
        logger.warning("Images directory does not exist")
        return
    
    disk_images = {str(img.relative_to(".")) for img in images_dir.glob("*.png")}
    disk_images.update({str(img.relative_to(".")) for img in images_dir.glob("*.jpg")})
    disk_images.update({str(img.relative_to(".")) for img in images_dir.glob("*.jpeg")})
    
    logger.info(f"Found {len(disk_images)} images on disk")
    
    # Find orphaned images
    orphaned = disk_images - db_images
    
    if not orphaned:
        logger.info("No orphaned images found")
        return
    
    logger.info(f"Found {len(orphaned)} orphaned images")
    
    total_size = 0
    for img_path in orphaned:
        size = Path(img_path).stat().st_size
        total_size += size
        logger.info(f"  - {img_path} ({size / 1024:.1f} KB)")
    
    logger.info(f"Total size: {total_size / (1024 * 1024):.2f} MB")
    
    if dry_run:
        logger.info("DRY RUN: No files deleted. Run with --delete to actually remove files.")
    else:
        for img_path in orphaned:
            Path(img_path).unlink()
            logger.info(f"Deleted: {img_path}")
        logger.info(f"Cleanup complete: {len(orphaned)} files deleted")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up orphaned images")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete files (default is dry-run)",
    )
    args = parser.parse_args()
    
    cleanup_orphaned_images(dry_run=not args.delete)
