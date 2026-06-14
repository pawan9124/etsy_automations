"""
Pinterest Pin Builder
─────────────────────
Composites vertical 9:16 pins (images and videos) for Pinterest marketing.
"""

import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageFilter

from config import PINTEREST_W, PINTEREST_H
from listing_engine.fonts import load_title_font, load_subtitle_font

logger = logging.getLogger("etsy_tumbler")

def create_blurred_background(source_img: Image.Image) -> Image.Image:
    """
    Creates a 1080x1920 blurred, darkened background from a source image.
    """
    # Crop and resize to 9:16
    bg = ImageOps.fit(source_img.convert("RGBA"), (PINTEREST_W, PINTEREST_H), centering=(0.5, 0.5))
    # Apply heavy blur
    bg = bg.filter(ImageFilter.GaussianBlur(radius=40))
    # Add dark overlay (60% opacity black)
    overlay = Image.new("RGBA", (PINTEREST_W, PINTEREST_H), (0, 0, 0, 150))
    return Image.alpha_composite(bg, overlay)


def _draw_pinterest_text(img: Image.Image, hook_text: str):
    """
    Draws the AI hook text at the top, and CTA at the bottom.
    """
    draw = ImageDraw.Draw(img)
    title_font = load_title_font(80)
    cta_font = load_subtitle_font(45)

    # Top Hook (word wrap)
    import textwrap
    lines = textwrap.wrap(hook_text.upper(), width=20)
    
    y_text = 150
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        x = (PINTEREST_W - tw) // 2
        
        # Draw soft shadow
        draw.text((x+3, y_text+3), line, font=title_font, fill=(0, 0, 0, 150))
        # Draw text
        draw.text((x, y_text), line, font=title_font, fill=(255, 255, 255))
        y_text += (bbox[3] - bbox[1]) + 20


def create_pinterest_image_pin(wrap_img: Image.Image, slide_img: Image.Image, hook_text: str, output_path: Path, slide_name: str = ""):
    """
    Creates a static vertical pin from an existing square Etsy slide.
    """
    bg = create_blurred_background(wrap_img)
    
    # If this is the 15-tumbler grid, don't stretch it so we don't cut off the edges
    if "11_flat_bundle_preview" in slide_name:
        target_w = PINTEREST_W
        paste_y = (PINTEREST_H - target_w) // 2 + 100  # Shift down slightly to clear top text
    else:
        # Zoom in: Resize the square slide to be larger than the canvas width
        target_w = PINTEREST_W + 400
        paste_y = 350  # Shift down so the massive zoomed image doesn't overlap top text

    slide_resized = slide_img.resize((target_w, target_w), Image.Resampling.LANCZOS)
    
    # Paste slide in the center horizontally
    paste_x = (PINTEREST_W - target_w) // 2
    bg.paste(slide_resized, (paste_x, paste_y), slide_resized if slide_resized.mode == "RGBA" else None)
    
    _draw_pinterest_text(bg, hook_text)
    
    bg.convert("RGB").save(output_path, quality=90)
    logger.info("  [Pinterest] Saved static pin -> %s", output_path.name)


def create_pinterest_video_pin(wrap_img: Image.Image, rotating_video_path: Path, hook_text: str, output_path: Path):
    """
    Creates a vertical video pin using the rotating 360 video over a blurred background.
    """
    # 1. Create the background image with baked-in text
    bg = create_blurred_background(wrap_img)
    _draw_pinterest_text(bg, hook_text)
    
    temp_bg_path = rotating_video_path.parent / "temp_pin_bg.png"
    bg.convert("RGB").save(temp_bg_path)
    
    # 2. Use moviepy to composite
    from moviepy import ImageClip, VideoFileClip, CompositeVideoClip
    
    try:
        video_clip = VideoFileClip(str(rotating_video_path))
        
        # Zoom in: Ensure video is square and fits horizontally larger than full width
        target_w = PINTEREST_W + 400
        aspect = video_clip.w / video_clip.h
        target_h = int(target_w / aspect)
        
        video_clip = video_clip.resized(width=target_w)
        
        bg_clip = ImageClip(str(temp_bg_path)).with_duration(video_clip.duration)
        
        # Move the video down so it doesn't overlap the text at the top
        final_video = CompositeVideoClip([
            bg_clip,
            video_clip.with_position(("center", 350))
        ])
        
        logger.info("  [Pinterest] Rendering video pin -> %s", output_path.name)
        final_video.write_videofile(
            str(output_path),
            codec="libx264",
            audio=False,
            fps=30,
            logger=None
        )
        
    except Exception as e:
        logger.error("  [Pinterest] Failed to render video pin: %s", e)
    finally:
        if temp_bg_path.exists():
            temp_bg_path.unlink()
