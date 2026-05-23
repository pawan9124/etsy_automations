"""
Mockup Engine — Displacement map compositing for tumbler mockups.

Uses OpenCV cv2.remap() for high-quality bilinear displacement warping
and Image.blend() for realistic tumbler surface blending.

This replicates Photoshop smart-object mockup behavior using
vectorized NumPy for map generation + OpenCV for interpolation.
"""

import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageChops

logger = logging.getLogger("etsy_tumbler")

# Default displacement intensity (pixels of max horizontal shift)
DEFAULT_DISPLACEMENT_STRENGTH = 40
# Default glass shine opacity (screen blend)
DEFAULT_GLASS_OPACITY = 0.75


def _detect_focal_x(image: Image.Image) -> int:
    """
    Find the horizontal location of the visually striking content in an
    artwork. Uses a saturation+luminance score so it picks the subject
    (e.g. a face) rather than a uniformly-bright background. Falls back
    to the geometric center if nothing dominant is found.
    """
    arr = np.array(image.convert("RGB"), dtype=np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    luma = (r + g + b) / 3.0
    sat = arr.max(axis=2) - arr.min(axis=2)
    score = luma * 0.6 + sat * 1.4
    col_score = score.sum(axis=0)
    win = max(50, image.width // 16)
    kernel = np.ones(win, dtype=np.float32) / win
    smoothed = np.convolve(col_score, kernel, mode="same")
    return int(smoothed.argmax())


def _create_single_tumbler_view(
    base_image: Image.Image,
    design_wrap: Image.Image,
    mask_pil: Image.Image,
    disp_pil: Image.Image,
    glass_pil: Image.Image = None,
    strength: float = DEFAULT_DISPLACEMENT_STRENGTH,
    glass_opacity: float = DEFAULT_GLASS_OPACITY,
    crop_mode: str = "full",
) -> Image.Image | None:
    """
    Creates one blended view of a tumbler using cv2.remap() for
    high-quality displacement and ImageChops.screen() for realistic shine.

    Parameters
    ----------
    base_image : PIL.Image — background scene (RGBA)
    design_wrap : PIL.Image — flat wrap design (RGBA)
    mask_pil : PIL.Image — grayscale mask ("L" mode)
    disp_pil : PIL.Image — grayscale displacement map ("L" mode)
    glass_pil: PIL.Image — grayscale or RGBA glass shine map
    strength : float — displacement intensity in pixels
    glass_opacity : float — strength of the screen blend shine
    crop_mode : str — "full", "left", "center", or "right"
                 For triple tumblers, crops 1/3 of the design.

    Returns
    -------
    PIL.Image — composited RGBA layer, or None on failure
    """
    # --- 1) Crop the design for panoramic views ---
    if crop_mode in ("left", "center", "right"):
        dw, dh = design_wrap.size
        half = dw // 2
        if crop_mode == "left":
            crop_box = (0, 0, half, dh)
        elif crop_mode == "center":
            # Center the crop on the visually striking part of the artwork,
            # not just the geometric middle. This keeps the subject's face/
            # focal element aligned with the visible tumbler face.
            focal_x = _detect_focal_x(design_wrap)
            x1 = max(0, min(dw - half, focal_x - half // 2))
            crop_box = (x1, 0, x1 + half, dh)
        else:  # right
            crop_box = (half, 0, dw, dh)
        design_view = design_wrap.crop(crop_box)
    else:
        design_view = design_wrap

    # --- 2) Find mask bounding box ---
    mask_bbox = mask_pil.getbbox()
    if not mask_bbox:
        return None

    target_w = mask_bbox[2] - mask_bbox[0]
    target_h = mask_bbox[3] - mask_bbox[1]

    # --- 3) Resize design preserving aspect ratio ---
    aspect_ratio = design_view.width / design_view.height
    new_h = target_h
    new_w = int(new_h * aspect_ratio)
    resized_design = design_view.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Place onto a full-size canvas centered within the mask region
    canvas = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    paste_x = mask_bbox[0] + (target_w - new_w) // 2
    paste_y = mask_bbox[1]
    canvas.paste(resized_design, (paste_x, paste_y))

    # --- 4) Apply cv2.remap() displacement ---
    design_cv = cv2.cvtColor(np.array(canvas), cv2.COLOR_RGBA2BGRA)
    disp_cv = np.array(disp_pil, dtype=np.int16)
    h, w = disp_cv.shape[:2]

    # Build remap coordinate grids (vectorized — no Python loops)
    yy, xx = np.mgrid[0:h, 0:w]
    map_y = yy.astype(np.float32)
    map_x = xx.astype(np.float32)

    # Apply horizontal displacement from the grayscale map
    offset = (disp_cv.astype(np.float32) - 128.0) / 128.0
    map_x += offset * strength

    # cv2.remap with bilinear interpolation for smooth warping
    warped_cv = cv2.remap(
        design_cv, map_x, map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )
    warped_pil = Image.fromarray(cv2.cvtColor(warped_cv, cv2.COLOR_BGRA2RGBA))

    # --- 5) Composite onto base ---
    result = base_image.copy()
    result.paste(warped_pil, (0, 0), mask_pil)

    # --- 6) Apply Screen Blend Glass Layer ---
    if glass_pil:
        original_alpha = result.getchannel('A')
        
        if glass_pil.mode != "RGBA":
            glass_pil = glass_pil.convert("RGBA")
            
        screened_result = ImageChops.screen(result, glass_pil)
        result = Image.blend(result, screened_result, glass_opacity)
        result.putalpha(original_alpha)

    return result


def apply_displacement(
    artwork: Image.Image,
    base: Image.Image,
    mask_pil: Image.Image,
    disp_pil: Image.Image,
    glass_pil: Image.Image = None,
    strength: float = DEFAULT_DISPLACEMENT_STRENGTH,
    glass_opacity: float = DEFAULT_GLASS_OPACITY,
) -> Image.Image:
    """High-level single mockup wrapper."""
    result = base.convert("RGBA")

    blended_layer = _create_single_tumbler_view(
        result, artwork.convert("RGBA"),
        mask_pil, disp_pil, glass_pil,
        strength, glass_opacity, crop_mode="full",
    )

    return blended_layer if blended_layer else result


def generate_mockup(
    artwork_path: Path,
    base_path: Path,
    mask_path: Path,
    displacement_path: Path,
    glass_path: Path = None,
    strength: float = DEFAULT_DISPLACEMENT_STRENGTH,
    glass_opacity: float = DEFAULT_GLASS_OPACITY,
) -> Image.Image:
    """
    Load all files and produce a composited single-tumbler mockup.
    """
    artwork = Image.open(artwork_path).convert("RGBA")
    base = Image.open(base_path).convert("RGBA")
    mask = Image.open(mask_path).convert("L").resize(base.size, Image.Resampling.LANCZOS)
    disp = Image.open(displacement_path).convert("L").resize(base.size, Image.Resampling.LANCZOS)
    
    glass = None
    if glass_path and glass_path.exists():
        glass = Image.open(glass_path).convert("RGBA").resize(base.size, Image.Resampling.LANCZOS)

    result = apply_displacement(artwork, base, mask, disp, glass, strength, glass_opacity)
    logger.info("  [MOCKUP] Generated mockup with %s", artwork_path.name)
    return result


def generate_cropped_single_tumbler(
    artwork_path: Path,
    mask_path: Path,
    displacement_path: Path,
    glass_path: Path,
    base_path: Path = None,
    strength: float = DEFAULT_DISPLACEMENT_STRENGTH,
    glass_opacity: float = DEFAULT_GLASS_OPACITY,
) -> Image.Image:
    """
    Generates a perfectly cropped, transparent 3D tumbler.
    Used for composing multi-tumbler grids (e.g. 15-pack slides).
    """
    artwork = Image.open(artwork_path).convert("RGBA")
    mask = Image.open(mask_path).convert("L")
    disp = Image.open(displacement_path).convert("L")
    glass = Image.open(glass_path).convert("RGBA")
    
    # Use the provided base (with lid/straw) or transparent base
    if base_path and base_path.exists():
        base = Image.open(base_path).convert("RGBA")
        
        # Remove the dark studio background so crops don't have a dark rectangular box behind them
        from PIL import ImageDraw
        ImageDraw.floodfill(base, (0, 0), (0, 0, 0, 0), thresh=30)
        ImageDraw.floodfill(base, (base.width - 1, 0), (0, 0, 0, 0), thresh=30)
        
        target_size = base.size
    else:
        target_size = mask.size
        base = Image.new("RGBA", target_size, (0, 0, 0, 0))

    if mask.size != target_size:
        mask = mask.resize(target_size, Image.Resampling.LANCZOS)
    if disp.size != target_size:
        disp = disp.resize(target_size, Image.Resampling.LANCZOS)
    if glass.size != target_size:
        glass = glass.resize(target_size, Image.Resampling.LANCZOS)

    # Apply standard 3D warping and glass shine
    blended_layer = _create_single_tumbler_view(
        base, artwork,
        mask, disp, glass,
        strength, glass_opacity, crop_mode="center",
    )
    
    if blended_layer is None:
        return base

    # Crop to the tumbler column using mask bounds.
    # blended_layer has an opaque background so getbbox() returns the full canvas;
    # the mask tells us exactly where the tumbler face sits.
    mask_bbox = mask.getbbox()
    if mask_bbox is None:
        return base
    W, H = blended_layer.size
    pad_x = max(20, int((mask_bbox[2] - mask_bbox[0]) * 0.08))
    crop_bbox = (
        max(0, mask_bbox[0] - pad_x),
        0,                                   # include straw from top
        min(W, mask_bbox[2] + pad_x),
        min(H, mask_bbox[3] + 20),
    )
    return blended_layer.crop(crop_bbox)


def generate_triple_mockup(
    artwork_paths: list[Path],
    base_path: Path,
    mask_paths: list[Path],
    displacement_paths: list[Path],
    glass_path: Path = None,
    strength: float = DEFAULT_DISPLACEMENT_STRENGTH,
    glass_opacity: float = DEFAULT_GLASS_OPACITY,
) -> Image.Image:
    """
    Generate a triple-tumbler mockup by compositing 3 artworks
    onto left/center/right positions.
    """
    base = Image.open(base_path).convert("RGBA")
    positions = ["center", "center", "center"]
    
    glass = None
    if glass_path and glass_path.exists():
        glass = Image.open(glass_path).convert("RGBA").resize(base.size, Image.Resampling.LANCZOS)

    for i, (art_p, mask_p, disp_p) in enumerate(
        zip(artwork_paths, mask_paths, displacement_paths)
    ):
        artwork = Image.open(art_p).convert("RGBA")
        mask = Image.open(mask_p).convert("L").resize(base.size, Image.Resampling.LANCZOS)
        disp = Image.open(disp_p).convert("L").resize(base.size, Image.Resampling.LANCZOS)
        pos = positions[i] if i < 3 else "full"

        blended_layer = _create_single_tumbler_view(
            base, artwork, mask, disp, glass,
            strength, glass_opacity, crop_mode=pos,
        )

        if blended_layer:
            # Overwrite base with the result of this tumbler
            base = blended_layer

        logger.info("  [MOCKUP] Triple %s: %s", pos, art_p.name)

    return base

