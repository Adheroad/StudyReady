#!/usr/bin/env python3
"""Cleanup old generated papers and images from the data directory.

This script is intended to be consistent with other maintenance scripts in the
project (e.g. cleanup_images.py). It removes:
  - Old exported papers from data/exports
  - Old images from data/images

By default it runs in DRY-RUN mode and only logs what would be deleted.
Use the --delete flag to actually remove files.
"""

import argparse
import sys
import time
from pathlib import Path

# Make Backend/ importable as a package root (same as cleanup_images.py)
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging import get_logger  # type: ignore

logger = get_logger(__name__)


def is_older_than(path: Path, max_age_seconds: float, now: float) -> bool:
    """Return True if the file's last-modified time exceeds `max_age_seconds`."""
    try:
        return now - path.stat().st_mtime > max_age_seconds
    except OSError:
        # If we cannot stat the file, treat it as not deletable
        return False


def cleanup_old_files(
    target_dirs: list[Path],
    max_age_days: int,
    dry_run: bool = True,
) -> None:
    """Delete files under `target_dirs` that are older than `max_age_days`."""
    now = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60

    logger.info(
        "%sCleanup started. Retention: %d day(s).",
        "[DRY-RUN] " if dry_run else "",
        max_age_days,
    )

    total_deleted = 0
    total_errors = 0

    for base_dir in target_dirs:
        if not base_dir.exists():
            logger.info("Skip missing directory: %s", base_dir)
            continue

        logger.info("Scanning directory: %s", base_dir)

        for path in base_dir.rglob("*"):
            # Only consider regular files
            if not path.is_file():
                continue

            # Skip symlinks for safety
            if path.is_symlink():
                logger.debug("Skipping symlink: %s", path)
                continue

            if not is_older_than(path, max_age_seconds, now):
                continue

            if dry_run:
                logger.info("[DRY-RUN] Would delete: %s", path)
                total_deleted += 1
                continue

            try:
                size_kb = path.stat().st_size / 1024
                path.unlink()
                logger.info("Deleted: %s (%.1f KB)", path, size_kb)
                total_deleted += 1
            except FileNotFoundError:
                logger.warning("Already removed (race condition?): %s", path)
            except PermissionError:
                logger.error("Permission denied: %s", path)
                total_errors += 1
            except OSError as exc:
                logger.error("OS error deleting %s: %s", path, exc)
                total_errors += 1

    logger.info(
        "Cleanup finished. %s %d file(s). Errors: %d.",
        "Would delete" if dry_run else "Deleted",
        total_deleted,
        total_errors,
    )


def main() -> None:

    # Use DATA_DIR from app config for consistency
    from app.config import get_settings
    settings = get_settings()
    data_dir = Path(settings.DATA_DIR)
    papers_dir = data_dir / "papers"
    images_dir = data_dir / "images"

    parser = argparse.ArgumentParser(
        description="Clean up old downloaded papers and images.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Retention window in days (default: 7). Files older than this are removed.",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete files (default is dry-run).",
    )

    args = parser.parse_args()

    cleanup_old_files(
        target_dirs=[papers_dir, images_dir],
        max_age_days=args.days,
        dry_run=not args.delete,
    )


if __name__ == "__main__":
    main()