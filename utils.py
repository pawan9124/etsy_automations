"""
Utility helpers — folder creation, logging setup, image validation.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from config import (
    INPUT_DIR, OUTPUT_DIR, LOG_DIR, TEMPLATES_DIR, SCRIPTS_DIR,
    LOG_FILENAME, LOG_LEVEL, SUPPORTED_EXTENSIONS, MIN_WIDTH_PX, MIN_HEIGHT_PX,
)


def setup_folders() -> None:
    """Create the base directory structure if it doesn't exist."""
    for folder in (INPUT_DIR, OUTPUT_DIR, LOG_DIR, TEMPLATES_DIR, SCRIPTS_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def setup_logging() -> logging.Logger:
    """Configure console + file logging and return the root logger."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOG_DIR / LOG_FILENAME
    fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger("etsy_tumbler")
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    logger.addHandler(ch)

    return logger


def ensure_output_dirs(bundle_name: str) -> tuple[Path, Path]:
    """
    Create and return (straight_dir, tapered_dir) for a given bundle.
    """
    straight_dir = OUTPUT_DIR / bundle_name / "straight_wraps"
    tapered_dir = OUTPUT_DIR / bundle_name / "tapered_wraps"
    straight_dir.mkdir(parents=True, exist_ok=True)
    tapered_dir.mkdir(parents=True, exist_ok=True)
    return straight_dir, tapered_dir


def collect_images(folder: Path) -> list[Path]:
    """Return sorted list of supported image files inside *folder*."""
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def validate_image(width: int, height: int, filepath: Path, logger: logging.Logger) -> bool:
    """
    Check that the source image meets the minimum resolution.
    Returns True if valid, False otherwise.
    """
    if width < MIN_WIDTH_PX or height < MIN_HEIGHT_PX:
        logger.warning(
            "SKIPPED %s — resolution %dx%d is below minimum %dx%d",
            filepath.name, width, height, MIN_WIDTH_PX, MIN_HEIGHT_PX,
        )
        return False
    return True
