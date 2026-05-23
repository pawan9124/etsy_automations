"""
Slide Generators — produces all 10 Etsy listing images.

Each function returns a PIL Image (2048x2048 RGBA).
"""

import logging
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

from listing_engine.fonts import load_title_font, load_subtitle_font, load_body_font
from listing_engine.mockup import generate_mockup, generate_triple_mockup, generate_cropped_single_tumbler
from listing_engine.palette import extract_palette

logger = logging.getLogger("etsy_tumbler")

# Canvas size matching upscaled mockup assets
CANVAS = 2048
BG_COLOR = (12, 12, 16, 255)          # near-black
ACCENT_COLOR = (201, 168, 76)          # antique gold
TEXT_COLOR = (240, 235, 225)           # warm white
SUBTLE_COLOR = (140, 135, 125)        # muted for subtitles
BORDER_COLOR = (50, 45, 40, 255)      # dark frame border


def _new_canvas(bg=BG_COLOR) -> Image.Image:
    """Create a fresh dark canvas."""
    return Image.new("RGBA", (CANVAS, CANVAS), bg)


def _draw_text_centered(draw, text, y, font, fill=TEXT_COLOR, canvas_w=CANVAS):
    """Draw text horizontally centered at vertical position y."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (canvas_w - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)


def _add_border_frame(img: Image.Image, thickness: int = 3, margin: int = 40) -> Image.Image:
    """Add a subtle decorative border around the image."""
    draw = ImageDraw.Draw(img)
    m = margin
    draw.rectangle(
        [m, m, CANVAS - m, CANVAS - m],
        outline=ACCENT_COLOR + (80,), width=thickness,
    )
    return img


def _add_slide_label(img: Image.Image, number: int, title: str, subtitle: str = "") -> Image.Image:
    """Add a number badge and title at the top of a slide."""
    draw = ImageDraw.Draw(img)
    title_font = load_subtitle_font(40)
    sub_font = load_body_font(24)

    _draw_text_centered(draw, title.upper(), 70, title_font, fill=ACCENT_COLOR)
    if subtitle:
        _draw_text_centered(draw, subtitle.upper(), 120, sub_font, fill=SUBTLE_COLOR)

    return img


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 01 — HERO IMAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_01_hero(
    wrap_paths: list[Path],
    base_path: Path,
    mask_paths: list[Path],
    disp_paths: list[Path],
    glass_path: Path,
    bundle_name: str,
    subtitle: str,
    tags: list[str],
    count: int = 15,
    tumbler_type: str = "20oz Skinny Tumbler",
) -> Image.Image:
    """Hero slide: triple tumbler mockup with dynamic title overlay."""
    selected_wraps = wrap_paths[:3]
    while len(selected_wraps) < 3:
        selected_wraps.append(selected_wraps[-1])

    mockup = generate_triple_mockup(
        artwork_paths=selected_wraps,
        base_path=base_path,
        mask_paths=mask_paths,
        displacement_paths=disp_paths,
        glass_path=glass_path,
    )

    # --- Dark gradient at top for text legibility ---
    # (bottom already has baked-in "15 TUMBLER WRAP BUNDLE / 20oz" labels)
    w, h = mockup.size
    grad_end = int(h * 0.20)
    overlay = Image.new("RGBA", mockup.size, (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(grad_end):
        alpha = int(200 * (1.0 - y / grad_end))
        draw_ov.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    mockup = Image.alpha_composite(mockup.convert("RGBA"), overlay)

    # --- Text layers (collection name + selling points only — no duplicate of bottom) ---
    draw = ImageDraw.Draw(mockup)
    title_font = load_title_font(64)
    sub_font = load_subtitle_font(26)
    body_font = load_body_font(20)
    cx = w // 2

    # Collection name — large gold, horizontally centered on the actual canvas
    _draw_text_centered(draw, bundle_name.upper(), int(h * 0.018), title_font, fill=ACCENT_COLOR, canvas_w=w)

    # Thin gold rule below title
    rule_y = int(h * 0.094)
    draw.line([(cx - 240, rule_y), (cx + 240, rule_y)], fill=ACCENT_COLOR + (110,), width=1)

    # Selling points
    _draw_text_centered(
        draw,
        "STRAIGHT  +  TAPERED  WRAP FORMATS",
        int(h * 0.106),
        sub_font,
        fill=TEXT_COLOR,
        canvas_w=w,
    )
    _draw_text_centered(
        draw,
        "HIGH-RESOLUTION  300 DPI   ·   PRINT-READY   ·   COMMERCIAL USE",
        int(h * 0.144),
        body_font,
        fill=SUBTLE_COLOR,
        canvas_w=w,
    )

    logger.info("  [SLIDE 01] Hero image — %s", bundle_name)
    return mockup


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 02 — BUNDLE GRID
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_02_bundle_grid(
    wrap_paths: list[Path],
    bg_path: Path,
    single_base: Path,
    single_mask: Path,
    single_disp: Path,
    single_glass: Path,
) -> Image.Image:
    """Grid of 15 transparent 3D tumblers placed on the bundle background."""
    canvas = Image.open(bg_path).convert("RGBA")
    cw, ch = canvas.size
    
    cols = 5
    rows = 3
    
    # Scale margins and heights relative to canvas size
    margin_top = int(ch * 0.20)
    margin_bottom = int(ch * 0.26)
    margin_side = int(cw * 0.22)  # Increased to keep tumblers away from left/right text
    
    avail_w = cw - 2 * margin_side
    avail_h = ch - margin_top - margin_bottom
    
    spacing_x = avail_w / (cols - 1) if cols > 1 else 0
    spacing_y = avail_h / (rows - 1) if rows > 1 else 0

    logger.info("  [SLIDE 02] Generating 15 3D tumblers for bundle grid...")
    
    # Scale tumbler height
    target_tumbler_height = int(ch * 0.24) 

    for i, wp in enumerate(wrap_paths[:15]):
        r, c = divmod(i, cols)
        
        # Center x, y for this grid cell
        cx = int(margin_side + c * spacing_x)
        cy = int(margin_top + r * spacing_y)
        
        try:
            # 1. Generate perfectly cropped transparent 3D tumbler
            tumbler_3d = generate_cropped_single_tumbler(
                artwork_path=wp,
                mask_path=single_mask,
                displacement_path=single_disp,
                glass_path=single_glass,
                base_path=single_base
            )
            
            # 2. Resize to fit grid cell
            aspect = tumbler_3d.width / tumbler_3d.height
            new_h = target_tumbler_height
            new_w = int(new_h * aspect)
            tumbler_thumb = tumbler_3d.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # 3. Paste onto canvas (using alpha channel as mask)
            paste_x = cx - new_w // 2
            paste_y = cy - new_h // 2
            canvas.paste(tumbler_thumb, (paste_x, paste_y), tumbler_thumb)
            
        except Exception as e:
            logger.error("    Failed to generate grid tumbler %d: %s", i, e)

    logger.info("  [SLIDE 02] Bundle grid complete.")
    return canvas


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 03 — CLOSE-UP DETAIL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_03_closeup(wrap_paths: list[Path], bg_path: Path) -> Image.Image:
    """Zoomed-in crop of the most detailed artwork."""
    canvas = Image.open(bg_path).convert("RGBA")
    cw, ch = canvas.size

    wp = wrap_paths[0] if wrap_paths else None
    if wp is None:
        return canvas

    img = Image.open(wp).convert("RGBA")
    w, h = img.size

    # Center crop at 2x zoom
    crop_w, crop_h = w // 2, h // 2
    left = (w - crop_w) // 2
    top = (h - crop_h) // 2
    cropped = img.crop((left, top, left + crop_w, top + crop_h))

    # Resize to fill display area (approximate based on a standard square area)
    # The production background usually has a square frame area
    display_size = int(cw * 0.7)
    cropped = cropped.resize((display_size, display_size), Image.Resampling.LANCZOS)

    offset_x = (cw - display_size) // 2
    offset_y = (ch - display_size) // 2
    
    # Optional drop shadow for the closeup image
    shadow = Image.new("RGBA", (display_size + 20, display_size + 20), (0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    canvas.paste(shadow, (offset_x - 10, offset_y - 10), shadow)

    canvas.paste(cropped, (offset_x, offset_y), cropped)

    logger.info("  [SLIDE 03] Close-up detail")
    return canvas


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 04 — FLAT WRAP PREVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_04_flat_wrap(wrap_path: Path, bg_path: Path) -> Image.Image:
    """Show the flat wrap design."""
    canvas = Image.open(bg_path).convert("RGBA")
    cw, ch = canvas.size

    img = Image.open(wrap_path).convert("RGBA")

    # Scale to fit with padding within the template
    max_w = int(cw * 0.8)
    max_h = int(ch * 0.5)
    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    iw, ih = img.size

    x = (cw - iw) // 2
    y = (ch - ih) // 2

    # Drop shadow
    shadow = Image.new("RGBA", (iw + 20, ih + 20), (0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    canvas.paste(shadow, (x + 5, y + 5), shadow)

    canvas.paste(img, (x, y), img)

    logger.info("  [SLIDE 04] Flat wrap preview")
    return canvas


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 05 — LIFESTYLE MOCKUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_05_lifestyle(
    wrap_path: Path,
    base_path: Path,
    mask_path: Path,
    disp_path: Path,
    glass_path: Path,
) -> Image.Image:
    """Lifestyle mockup using production assets."""
    mockup = generate_mockup(wrap_path, base_path, mask_path, disp_path, glass_path)
    
    logger.info("  [SLIDE 05] Lifestyle mockup")
    return mockup


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 06 — WHAT YOU WILL GET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_06_what_you_get(
    wrap_path: Path,
    base_path: Path,
    mask_path: Path,
    disp_path: Path,
    glass_path: Path,
) -> Image.Image:
    """Infographic / What you get slide using production assets."""
    mockup = generate_mockup(wrap_path, base_path, mask_path, disp_path, glass_path)
    logger.info("  [SLIDE 06] What you get (infographic)")
    return mockup


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 07 — COLOR PALETTE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_07_color_palette(wrap_paths: list[Path], bg_path: Path, palette_override: list[dict] | None = None) -> Image.Image:
    """Display extracted color palette for the bundle on a custom background."""
    canvas = Image.open(bg_path).convert("RGBA")
    cw, ch = canvas.size

    colors = []
    if palette_override:
        colors = palette_override
    else:
        # Extract a massive palette then filter down to 6 distinct ones
        raw_colors = extract_palette(wrap_paths, n_colors=12)
        if len(raw_colors) > 6:
            colors = raw_colors[:6]
        else:
            colors = raw_colors

    logger.info("  [PALETTE] Extracted %d colors from %d images", len(colors), len(wrap_paths))

    if not colors:
        return canvas

    draw = ImageDraw.Draw(canvas)
    
    # Left column for colors
    start_x = int(cw * 0.15)
    start_y = int(ch * 0.25)
    swatch_r = int(cw * 0.04) # radius
    gap_y = int(ch * 0.10)
    
    # Draw swatches and names
    name_font = load_subtitle_font(24)
    for i, color_data in enumerate(colors):
        cy = start_y + i * gap_y
        
        # Shadow
        shadow = Image.new("RGBA", (swatch_r * 2 + 10, swatch_r * 2 + 10), (0, 0, 0, 100))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        canvas.paste(shadow, (start_x - swatch_r - 5, cy - swatch_r - 5), shadow)

        # Swatch
        draw.ellipse([start_x - swatch_r, cy - swatch_r, start_x + swatch_r, cy + swatch_r], fill=color_data["rgb"])
        # Ring
        draw.ellipse([start_x - swatch_r, cy - swatch_r, start_x + swatch_r, cy + swatch_r], outline=ACCENT_COLOR, width=3)
        
        # Text to the right
        text_x = start_x + swatch_r + 30
        text = color_data.get("name", color_data["hex"]).upper()
        draw.text((text_x, cy - 12), text, font=name_font, fill=TEXT_COLOR)

    # Right side: Circular design
    if wrap_paths:
        design = Image.open(wrap_paths[0]).convert("RGBA")
        dw, dh = design.size
        size = min(dw, dh)
        left = (dw - size) // 2
        top = (dh - size) // 2
        cropped = design.crop((left, top, left + size, top + size))
        
        target_size = int(cw * 0.6)
        cropped = cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)
        
        mask = Image.new("L", (target_size, target_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, target_size, target_size), fill=255)
        
        paste_x = int(cw * 0.45)
        paste_y = int(ch * 0.15)
        canvas.paste(cropped, (paste_x, paste_y), mask)

    logger.info("  [SLIDE 07] Color palette (%d colors)", len(colors))
    return canvas


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 08 — SIZE GUIDE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_08_size_guide(wrap_path: Path, bg_path: Path) -> Image.Image:
    """Size guide visualization using custom background."""
    canvas = Image.open(bg_path).convert("RGBA")
    cw, ch = canvas.size
    
    # Load wrap
    wrap = Image.open(wrap_path).convert("RGBA")
    
    # Box bounds
    target_w = int(cw * 0.46)
    target_h = int(target_w * (8.2 / 9.3))
    
    wrap = wrap.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    x = int(cw * 0.395)
    y = int(ch * 0.258)
    
    canvas.paste(wrap, (x, y), wrap)

    logger.info("  [SLIDE 08] Size guide")
    return canvas


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 09 — MULTI TUMBLER DISPLAY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_09_multi_tumbler(
    wrap_paths: list[Path],
    bg_path: Path,
    single_base: Path,
    single_mask: Path,
    single_disp: Path,
    single_glass: Path,
) -> Image.Image:
    """Multi-tumbler layout display using cropped 3D tumblers."""
    canvas = Image.open(bg_path).convert("RGBA")
    cw, ch = canvas.size
    
    cols = 4
    n = len(wrap_paths)
    if n >= cols:
        step = max(1, n // cols)
        selected = [wrap_paths[i * step] for i in range(cols)]
    else:
        selected = wrap_paths[:cols]
        while len(selected) < cols:
            selected.append(selected[0])

    logger.info("  [SLIDE 09] Generating %d 3D tumblers for multi row...", cols)
    
    # Tumblers close together
    margin_side = int(cw * 0.18)
    cy = int(ch * 0.55) # Center Y moved up slightly to avoid bottom text
    target_tumbler_height = int(ch * 0.55)
    
    avail_w = cw - 2 * margin_side
    spacing_x = avail_w / (cols - 1) if cols > 1 else 0

    for i, wp in enumerate(selected):
        cx = int(margin_side + i * spacing_x)
        
        try:
            # Generate 3D cropped tumbler
            tumbler_3d = generate_cropped_single_tumbler(
                artwork_path=wp,
                mask_path=single_mask,
                displacement_path=single_disp,
                glass_path=single_glass,
                base_path=single_base
            )
            
            # Resize
            aspect = tumbler_3d.width / tumbler_3d.height
            new_h = target_tumbler_height
            new_w = int(new_h * aspect)
            tumbler_thumb = tumbler_3d.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Paste
            paste_x = cx - new_w // 2
            paste_y = cy - new_h // 2
            canvas.paste(tumbler_thumb, (paste_x, paste_y), tumbler_thumb)
            
        except Exception as e:
            logger.error("    Failed to generate row tumbler %d: %s", i, e)

    logger.info("  [SLIDE 09] Multi-tumbler display complete")
    return canvas


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 10 — THANK YOU / CTA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_10_thank_you(
    shop_name: str,
    shop_tagline: str,
    bg_path: Path,
) -> Image.Image:
    """Thank you / branding / CTA slide."""
    canvas = Image.open(bg_path).convert("RGBA")
    logger.info("  [SLIDE 10] Thank you / CTA")
    return canvas


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 11 — FLAT BUNDLE PREVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def slide_11_flat_bundle_preview(wrap_paths: list[Path], bg_path: Path) -> Image.Image:
    """Grid of up to 16 flat wraps placed on the bundle background."""
    canvas = Image.open(bg_path).convert("RGBA")
    cw, ch = canvas.size
    
    # Issue 2 Fix: Deduplicate exactly identical images based on file size
    unique_wraps = []
    seen_sizes = set()
    for wp in wrap_paths:
        sz = wp.stat().st_size
        if sz not in seen_sizes:
            seen_sizes.add(sz)
            unique_wraps.append(wp)
            
    n_wraps = min(len(unique_wraps), 16)
    items = unique_wraps[:n_wraps]

    if not items:
        return canvas

    # Issue 1 Fix: 4-column layout optimally fills the horizontal AND vertical space.
    cols = 4 
    rows = (n_wraps + cols - 1) // cols
    
    margin_top = int(ch * 0.15)
    margin_bottom = int(ch * 0.08)
    margin_side = int(cw * 0.06)
    
    avail_w = cw - 2 * margin_side
    avail_h = ch - margin_top - margin_bottom

    logger.info("  [SLIDE 11] Generating %d flat wraps for bundle preview...", n_wraps)

    first_wrap = Image.open(items[0])
    aspect = first_wrap.width / first_wrap.height
    
    gap_ratio = 0.05
    
    max_w_from_w = avail_w / (cols + (cols - 1) * gap_ratio)
    max_h_from_w = max_w_from_w / aspect
    
    max_h_from_h = avail_h / (rows + (rows - 1) * gap_ratio)
    max_w_from_h = max_h_from_h * aspect
    
    if max_h_from_w * (rows + (rows - 1) * gap_ratio) <= avail_h:
        new_w = int(max_w_from_w)
        new_h = int(max_h_from_w)
    else:
        new_w = int(max_w_from_h)
        new_h = int(max_h_from_h)
        
    gap_x = int(new_w * gap_ratio)
    gap_y = int(new_h * gap_ratio)
    
    total_h = rows * new_h + (rows - 1) * gap_y
    start_y = margin_top + (avail_h - total_h) // 2

    for r in range(rows):
        row_items = items[r * cols : (r + 1) * cols]
        row_cols = len(row_items)
        
        row_w = row_cols * new_w + (row_cols - 1) * gap_x
        start_x = margin_side + (avail_w - row_w) // 2
        y = start_y + r * (new_h + gap_y)
        
        for c, wp in enumerate(row_items):
            x = start_x + c * (new_w + gap_x)
            
            try:
                wrap = Image.open(wp).convert("RGBA")
                wrap_thumb = wrap.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                shadow = Image.new("RGBA", (new_w + 20, new_h + 20), (0, 0, 0, 60))
                shadow = shadow.filter(ImageFilter.GaussianBlur(8))
                canvas.paste(shadow, (int(x) - 10, int(y) - 10), shadow)
                
                canvas.paste(wrap_thumb, (int(x), int(y)), wrap_thumb)
                
            except Exception as e:
                logger.error("  [ERROR] Failed to load %s for flat grid: %s", wp.name, e)

    logger.info("  [SLIDE 11] Flat bundle grid complete.")
    return canvas
