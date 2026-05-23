"""
Etsy Tumbler Wrap Automation — Main Entry Point
===================================================

Usage:
    python main.py                          # process ALL bundles (wraps + listings)
    python main.py eternal_moon_bundle      # single bundle (wraps + listings)
    python main.py --wraps                  # wraps only (no listing images)
    python main.py --listing                # listing images only (no wraps)
    python main.py eternal_moon_bundle --listing   # single bundle, listing only

Drop your artwork PNGs into  input/<bundle_name>/  and run this script.
"""

import sys
import time

from PIL import Image

from config import INPUT_DIR, DPI
from utils import setup_folders, setup_logging, ensure_output_dirs, collect_images, validate_image
from processor import process_image
from drive_uploader import upload_bundle_to_drive
from pdf_generator import generate_download_pdf


def process_bundle_wraps(bundle_dir, logger):
    """Process every valid image inside one bundle folder into wraps."""
    bundle_name = bundle_dir.name
    logger.info("-" * 60)
    logger.info("[WRAPS] %s", bundle_name)

    images = collect_images(bundle_dir)
    if not images:
        logger.warning("   No supported images found -- skipping.")
        return 0, 0

    straight_dir, tapered_dir = ensure_output_dirs(bundle_name)

    success = 0
    skipped = 0

    for idx, img_path in enumerate(images, start=1):
        logger.info("  [%d/%d] %s", idx, len(images), img_path.name)

        # Quick resolution check without loading full image data
        with Image.open(img_path) as im:
            w, h = im.size
            if not validate_image(w, h, img_path, logger):
                skipped += 1
                continue

        if process_image(img_path, straight_dir, tapered_dir, idx):
            success += 1
        else:
            skipped += 1

    logger.info("   Done: %d processed, %d skipped", success, skipped)
    return success, skipped


def process_bundle_listing(bundle_dir, logger):
    """Generate 10 Etsy listing images for a bundle."""
    from listing_engine.generator import generate_listing_images

    logger.info("-" * 60)
    logger.info("[LISTING] %s", bundle_dir.name)

    saved = generate_listing_images(bundle_dir)
    logger.info("   Generated %d listing slides", len(saved))
    return len(saved)


def main():
    setup_folders()
    logger = setup_logging()

    # Parse arguments
    args = sys.argv[1:]
    do_wraps = True
    do_listing = True
    target = None

    for arg in args:
        if arg == "--wraps":
            do_listing = False
        elif arg == "--listing":
            do_wraps = False
        elif not arg.startswith("--"):
            target = arg

    logger.info("=" * 60)
    logger.info(">> Etsy Tumbler Wrap Automation")
    mode_parts = []
    if do_wraps:
        mode_parts.append("Wraps")
    if do_listing:
        mode_parts.append("Listing Images")
    logger.info("   Mode: %s | DPI: %d", " + ".join(mode_parts), DPI)
    logger.info("=" * 60)

    # Determine which bundles to process
    if target:
        bundles = [INPUT_DIR / target]
        if not bundles[0].is_dir():
            logger.error("Bundle folder not found: %s", bundles[0])
            sys.exit(1)
    else:
        bundles = sorted(
            d for d in INPUT_DIR.iterdir() if d.is_dir()
        )

    if not bundles:
        logger.warning("No bundle folders found in %s", INPUT_DIR)
        logger.info("Create a subfolder, drop your PNGs in, and re-run.")
        sys.exit(0)

    t0 = time.perf_counter()
    total_wraps_ok, total_wraps_skip = 0, 0
    total_listing = 0

    for bundle_dir in bundles:
        if do_wraps:
            ok, skip = process_bundle_wraps(bundle_dir, logger)
            total_wraps_ok += ok
            total_wraps_skip += skip

        if do_listing:
            n = process_bundle_listing(bundle_dir, logger)
            total_listing += n

        # Upload straight_wraps + tapered_wraps to Google Drive
        drive_link = upload_bundle_to_drive(bundle_dir.name)

        # Generate download_instruction.pdf with the Drive link
        generate_download_pdf(bundle_dir.name, drive_link)

    elapsed = time.perf_counter() - t0

    logger.info("=" * 60)
    if do_wraps:
        logger.info("WRAPS: %d processed, %d skipped", total_wraps_ok, total_wraps_skip)
    if do_listing:
        logger.info("LISTING: %d slides generated", total_listing)
    logger.info("TOTAL TIME: %.1fs", elapsed)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
