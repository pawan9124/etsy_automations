"""
Font management — load TTF fonts for Pillow text rendering.
"""

from pathlib import Path
from PIL import ImageFont

FONT_DIR = Path(__file__).parent / "assets" / "fonts"

# Fallback chain: Google Font → Windows system font → Pillow default
_FALLBACK_SYSTEM = "C:/Windows/Fonts/arial.ttf"


def _resolve(name: str) -> str:
    """Return absolute path to a font file, checking FONT_DIR then system."""
    local = FONT_DIR / name
    if local.exists():
        return str(local)
    if Path(_FALLBACK_SYSTEM).exists():
        return _FALLBACK_SYSTEM
    return ""


def load_title_font(size: int = 72) -> ImageFont.FreeTypeFont:
    """Cinzel Decorative Bold — for collection names."""
    path = _resolve("CinzelDecorative-Bold.ttf")
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def load_subtitle_font(size: int = 36) -> ImageFont.FreeTypeFont:
    """Cinzel Variable — for subtitles and labels."""
    path = _resolve("Cinzel-Variable.ttf")
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def load_body_font(size: int = 28) -> ImageFont.FreeTypeFont:
    """Inter — for body text, specs, and small labels."""
    path = _resolve("Inter-Variable.ttf")
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()
