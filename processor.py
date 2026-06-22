"""
Image processor — resizes artwork into straight & tapered 20 oz tumbler wraps.

Resize strategies (configured via RESIZE_MODE in config.py):
  * "cover"   — Scale to COVER the target, centre-crop.  Fast, but may clip edges.
  * "contain" — Scale to FIT entirely + blurred edge extension.  Zero clipping.  [DEFAULT]
  * "fit"     — Scale to FIT entirely, pad remaining space with black.  No clipping.

Other design decisions:
  * We use Pillow’s LANCZOS resampling (highest-quality downscale).
  * DPI metadata is embedded so print shops get the right size.
  * Tapered wraps are output as a TRAPEZOID (wider top, narrower bottom)
    with transparent corners — ready for sublimation / cutting templates.
"""

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np

from config import (
    DPI,
    RESAMPLE_FILTER,
    RESIZE_MODE,
    STRAIGHT_WIDTH_PX, STRAIGHT_HEIGHT_PX,
    TAPERED_WIDTH_PX, TAPERED_HEIGHT_PX, TAPERED_BOTTOM_WIDTH_PX,
    STRAIGHT_SUFFIX, TAPERED_SUFFIX,
    OUTPUT_FORMAT,
)

logger = logging.getLogger("etsy_tumbler")

# Map config string to Pillow constant
_RESAMPLE = getattr(Image.Resampling, RESAMPLE_FILTER, Image.Resampling.LANCZOS)


# ─── Strategy 1: COVER (scale to fill, centre-crop) ─────────────
def _cover_resize_and_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Scale *img* to fully COVER the target, then centre-crop.
    Fast and clean, but may clip edges when aspect ratios differ.
    """
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    resized = img.resize((new_w, new_h), _RESAMPLE)
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


# ─── Strategy 2: CONTAIN (fit + blurred edge extension) ──────────
def _contain_and_extend(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Scale *img* to FIT entirely (zero clipping), then fill remaining
    edge strips with a blurred version of the artwork.  A gradient
    mask ensures the seam is invisible.
    """
    src_w, src_h = img.size

    contain_scale = min(target_w / src_w, target_h / src_h)
    new_w = int(src_w * contain_scale)
    new_h = int(src_h * contain_scale)

    # If source already covers, just centre-crop
    if new_w >= target_w and new_h >= target_h:
        return _cover_resize_and_crop(img, target_w, target_h)

    fitted = img.resize((new_w, new_h), _RESAMPLE)

    # Background: cover-resize → centre-crop → heavy blur
    cover_scale = max(target_w / src_w, target_h / src_h)
    bg_w = int(src_w * cover_scale)
    bg_h = int(src_h * cover_scale)
    bg = img.resize((bg_w, bg_h), _RESAMPLE)
    bx = (bg_w - target_w) // 2
    by = (bg_h - target_h) // 2
    bg = bg.crop((bx, by, bx + target_w, by + target_h))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=25))

    # Gradient mask for seamless blending
    BLEND_ZONE = 50
    bz = min(BLEND_ZONE, new_w // 4, new_h // 4)
    arr = np.full((new_h, new_w), 255, dtype=np.uint8)
    for i in range(bz):
        v = int(255 * i / bz)
        arr[:, i]              = np.minimum(arr[:, i], v)
        arr[:, new_w - 1 - i]  = np.minimum(arr[:, new_w - 1 - i], v)
        arr[i, :]              = np.minimum(arr[i, :], v)
        arr[new_h - 1 - i, :]  = np.minimum(arr[new_h - 1 - i, :], v)
    mask = Image.fromarray(arr, "L")

    # Composite
    paste_x = (target_w - new_w) // 2
    paste_y = (target_h - new_h) // 2
    bg_rgba     = bg.convert("RGBA")
    fitted_rgba = fitted.convert("RGBA")
    bg_rgba.paste(fitted_rgba, (paste_x, paste_y), mask)
    return bg_rgba.convert("RGB")


# ─── Strategy 3: FIT (fit + solid black padding) ─────────────────
def _fit_and_pad(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Scale *img* to FIT entirely (zero clipping), pad remaining
    space with solid black.  Simple and safe, but visible bars.
    """
    fitted = ImageOps.contain(img, (target_w, target_h), _RESAMPLE)
    canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
    paste_x = (target_w - fitted.width) // 2
    paste_y = (target_h - fitted.height) // 2
    if fitted.mode == "RGBA":
        canvas.paste(fitted, (paste_x, paste_y), fitted)
    else:
        canvas.paste(fitted, (paste_x, paste_y))
    return canvas


# ─── Strategy 4: STRETCH (direct resize, ignore aspect ratio) ─────
def _stretch_to_fit(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Directly resize *img* to the exact target dimensions.
    This is what Photoshop does — for tumbler wraps where the
    aspect-ratio difference is only ~6%, the distortion is
    completely imperceptible, especially on a curved surface.
    """
    return img.resize((target_w, target_h), _RESAMPLE)


# ─── Dispatcher ──────────────────────────────────────────────────
_STRATEGIES = {
    "stretch": _stretch_to_fit,
    "cover":   _cover_resize_and_crop,
    "contain": _contain_and_extend,
    "fit":     _fit_and_pad,
}

def _resize_artwork(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Route to the resize strategy selected in config.py."""
    fn = _STRATEGIES.get(RESIZE_MODE, _stretch_to_fit)
    return fn(img, target_w, target_h)


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
    result = _resize_artwork(img, STRAIGHT_WIDTH_PX, STRAIGHT_HEIGHT_PX)
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
    result = _resize_artwork(img, TAPERED_WIDTH_PX, TAPERED_HEIGHT_PX)

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
