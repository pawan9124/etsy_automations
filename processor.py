"""
Image processor — resizes artwork into straight & tapered 20 oz tumbler wraps.

Design decisions:
  * We use Pillow's LANCZOS resampling (highest-quality downscale).
  * The source image is resized to COVER the target canvas
    (no white bars), then center-cropped.
  * DPI metadata is embedded so print shops get the right size.
  * Tapered wraps are output as a TRAPEZOID (wider top, narrower bottom)
    with transparent corners — ready for sublimation / cutting templates.
"""

import logging
from pathlib import Path

from PIL import Image, ImageDraw

from config import (
    DPI,
    RESAMPLE_FILTER,
    STRAIGHT_WIDTH_PX, STRAIGHT_HEIGHT_PX,
    TAPERED_WIDTH_PX, TAPERED_HEIGHT_PX, TAPERED_BOTTOM_WIDTH_PX,
    STRAIGHT_SUFFIX, TAPERED_SUFFIX,
    OUTPUT_FORMAT,
)

logger = logging.getLogger("etsy_tumbler")

# Map config string to Pillow constant
_RESAMPLE = getattr(Image.Resampling, RESAMPLE_FILTER, Image.Resampling.LANCZOS)


def _cover_resize_and_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Resize *img* so it fully COVERS the target dimensions (no empty space),
    then center-crop to exact target size.  This preserves the artwork's
    aspect ratio as closely as possible while filling the canvas.
    """
    src_w, src_h = img.size
    # Scale factor to cover the target
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)

    resized = img.resize((new_w, new_h), _RESAMPLE)

    # Center crop
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    cropped = resized.crop((left, top, left + target_w, top + target_h))
    return cropped


def _save_png(img: Image.Image, path: Path) -> None:
    """Save image as high-quality PNG with DPI metadata."""
    img.save(
        path,
        format=OUTPUT_FORMAT,
        dpi=(DPI, DPI),
        optimize=False,       # avoid lossy optimizations
        compress_level=1,     # fast write, still lossless
    )


def make_straight_wrap(img: Image.Image, out_dir: Path, stem: str, index: int) -> Path:
    """Create a straight 20 oz tumbler wrap and return the saved path."""
    result = _cover_resize_and_crop(img, STRAIGHT_WIDTH_PX, STRAIGHT_HEIGHT_PX)
    filename = f"{stem}_{index:02d}{STRAIGHT_SUFFIX}.png"
    out_path = out_dir / filename
    _save_png(result, out_path)
    logger.info("  [OK] Straight wrap -> %s  (%dx%d)", filename, STRAIGHT_WIDTH_PX, STRAIGHT_HEIGHT_PX)
    return out_path


def make_tapered_wrap(img: Image.Image, out_dir: Path, stem: str, index: int) -> Path:
    """
    Create a tapered 20 oz tumbler wrap and return the saved path.

    The output is a TRAPEZOID shape on a transparent canvas:
      - Top edge  = full canvas width  (top circumference, ~9.45")
      - Bottom edge = narrower          (bottom circumference, ~8.65")
      - Corners outside the trapezoid are transparent.

    This matches how a tapered tumbler's surface unrolls flat —
    wider at the rim, narrower at the base.
    """
    # 1. Resize artwork to cover the full canvas (sized to widest dimension)
    result = _cover_resize_and_crop(img, TAPERED_WIDTH_PX, TAPERED_HEIGHT_PX)

    # 2. Convert to RGBA so we can apply transparency
    if result.mode != "RGBA":
        result = result.convert("RGBA")

    # 3. Build a trapezoidal alpha mask
    #    Top edge spans the full width; bottom edge is centered and narrower.
    offset = (TAPERED_WIDTH_PX - TAPERED_BOTTOM_WIDTH_PX) // 2

    mask = Image.new("L", (TAPERED_WIDTH_PX, TAPERED_HEIGHT_PX), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(
        [
            (0, 0),                                       # top-left
            (TAPERED_WIDTH_PX - 1, 0),                    # top-right
            (TAPERED_WIDTH_PX - 1 - offset, TAPERED_HEIGHT_PX - 1),  # bottom-right
            (offset, TAPERED_HEIGHT_PX - 1),              # bottom-left
        ],
        fill=255,
    )

    # 4. Apply the mask — areas outside the trapezoid become transparent
    result.putalpha(mask)

    # 5. Save
    filename = f"{stem}_{index:02d}{TAPERED_SUFFIX}.png"
    out_path = out_dir / filename
    _save_png(result, out_path)
    logger.info(
        "  [OK] Tapered  wrap -> %s  (top=%dpx, bottom=%dpx, h=%dpx)",
        filename, TAPERED_WIDTH_PX, TAPERED_BOTTOM_WIDTH_PX, TAPERED_HEIGHT_PX,
    )
    return out_path


def process_image(filepath: Path, straight_dir: Path, tapered_dir: Path, index: int) -> bool:
    """
    Open one image, produce both wrap versions, return True on success.
    """
    stem = filepath.stem  # e.g. "moon_ritual"
    try:
        with Image.open(filepath) as img:
            # Convert to RGB if necessary (handles RGBA, palette, etc.)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")

            make_straight_wrap(img, straight_dir, stem, index)
            make_tapered_wrap(img, tapered_dir, stem, index)
        return True
    except Exception as exc:
        logger.error("  [FAIL] Failed to process %s: %s", filepath.name, exc)
        return False
