"""
Listing Image Generator — Orchestrator.

Reads a bundle folder with wraps + bundle.json, generates all 10 listing images.

Usage:
    from listing_engine.generator import generate_listing_images
    generate_listing_images(Path("input/eternal_moon_bundle"))
"""

import json
import logging
import re
from pathlib import Path

from PIL import Image

from config import OUTPUT_DIR, SUPPORTED_EXTENSIONS, STRAIGHT_SUFFIX, TAPERED_SUFFIX
from listing_engine.ai_listing import generate_listing_copy
from listing_engine.slides import (
    slide_01_hero,
    slide_02_bundle_grid,
    slide_03_closeup,
    slide_04_flat_wrap,
    slide_05_lifestyle,
    slide_06_what_you_get,
    slide_07_color_palette,
    slide_08_size_guide,
    slide_09_multi_tumbler,
    slide_10_thank_you,
    slide_11_flat_bundle_preview,
)

logger = logging.getLogger("etsy_tumbler")

# Mockup asset directory (relative to project root)
MOCKUP_DIR = Path(__file__).parent.parent / "mockup_assets"

# Default bundle metadata
_DEFAULTS = {
    "bundle_name": "Collection",
    "subtitle": "Tumbler Wrap Bundle",
    "tumbler_type": "20oz Skinny Tumbler",
    "wrap_count": 15,
    "category": "Digital Art",
    "aesthetic_tags": ["Premium", "Unique", "Handcrafted"],
    "palette": None,
    "shop_name": "xfantasypro",
    "shop_tagline": "Premium Digital Designs",
}


import random

class WrapSelector:
    def __init__(self, wraps: list[Path]):
        self.all_wraps = wraps.copy()
        
        # Compile a regex to strip the output suffix added by processor.py
        # e.g. "Botanical Gothic Bundle (1)_1_01_straight" -> "Botanical Gothic Bundle (1)_1"
        pattern_str = r'_\d{2}(' + re.escape(STRAIGHT_SUFFIX) + r'|' + re.escape(TAPERED_SUFFIX) + r')$'
        self._pattern = re.compile(pattern_str)
        
        self.available_wraps = [w for w in wraps if not any(self._original_stem(w.stem).endswith(f"_{i}") for i in range(1, 11))]
        if not self.available_wraps:
            self.available_wraps = wraps.copy()
        random.shuffle(self.available_wraps)

    def _original_stem(self, stem: str) -> str:
        return self._pattern.sub('', stem)
        
    def get(self, suffix: str, count: int) -> list[Path]:
        matches = [w for w in self.all_wraps if self._original_stem(w.stem).endswith(suffix)]
        if matches:
            return matches
            
        selected = []
        for _ in range(count):
            if not self.available_wraps:
                self.available_wraps = self.all_wraps.copy()
                random.shuffle(self.available_wraps)
            selected.append(self.available_wraps.pop(0))
        return selected


def _folder_name_to_title(folder_name: str) -> str:
    """Convert folder name like 'eternal_moon_bundle' → 'Eternal Moon'."""
    name = re.sub(
        r'[\-_](bundle|pack|\d+pack|15pack|wraps?|collection|set)$',
        '', folder_name, flags=re.IGNORECASE,
    )
    return name.replace('_', ' ').replace('-', ' ').title()


def _load_bundle_meta(bundle_dir: Path) -> dict:
    """Load bundle.json or return defaults, deriving bundle_name from folder if absent."""
    meta_file = bundle_dir / "bundle.json"
    meta = dict(_DEFAULTS)
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            user_meta = json.load(f)
        meta.update(user_meta)
        logger.info("  Loaded bundle.json")
    else:
        meta["bundle_name"] = _folder_name_to_title(bundle_dir.name)
        logger.info("  No bundle.json — derived title: %s", meta["bundle_name"])
    return meta


def _collect_wraps(bundle_dir: Path) -> list[Path]:
    """
    Collect wrap images from the output straight_wraps directory if available.
    Otherwise, fall back to the input bundle directory.
    """
    straight_wraps_dir = OUTPUT_DIR / bundle_dir.name / "straight_wraps"
    if straight_wraps_dir.is_dir():
        search_dir = straight_wraps_dir
    else:
        wraps_dir = bundle_dir / "wraps"
        if wraps_dir.is_dir():
            search_dir = wraps_dir
        else:
            search_dir = bundle_dir

    wraps = sorted(
        p for p in search_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    return wraps


def _save_slide(img: Image.Image, out_dir: Path, filename: str) -> Path:
    """Save a listing slide image."""
    out_path = out_dir / filename
    img.save(out_path, format="PNG", dpi=(300, 300), compress_level=1)
    return out_path


def generate_listing_images(bundle_dir: Path) -> list[Path]:
    """
    Generate all 10 Etsy listing images for a bundle.

    Parameters
    ----------
    bundle_dir : Path — input bundle folder containing wraps + optional bundle.json

    Returns
    -------
    list[Path] — paths to the 10 generated listing images
    """
    logger.info("=" * 60)
    logger.info("LISTING ENGINE: %s", bundle_dir.name)
    logger.info("=" * 60)

    # Load metadata
    meta = _load_bundle_meta(bundle_dir)
    bundle_name = meta["bundle_name"]
    subtitle = meta["subtitle"]
    tags = meta.get("aesthetic_tags", [])
    shop_name = meta["shop_name"]
    shop_tagline = meta["shop_tagline"]
    wrap_count = meta.get("wrap_count", 15)

    # Collect wrap images
    wraps = _collect_wraps(bundle_dir)
    if not wraps:
        logger.error("No wrap images found in %s", bundle_dir)
        return []

    logger.info("  Found %d wrap images", len(wraps))

    # Parse palette override (if provided as list of dicts in JSON)
    palette_override = None
    if meta.get("palette"):
        palette_override = []
        for entry in meta["palette"]:
            hex_val = entry.get("hex", "#808080")
            r = int(hex_val[1:3], 16)
            g = int(hex_val[3:5], 16)
            b = int(hex_val[5:7], 16)
            palette_override.append({
                "name": entry.get("name", "Unknown"),
                "hex": hex_val,
                "rgb": (r, g, b),
            })

    # Output directory
    out_dir = OUTPUT_DIR / bundle_dir.name / "listing_images"
    out_dir.mkdir(parents=True, exist_ok=True)

    prod_dir = MOCKUP_DIR / "tumblers_production"
    
    # Blank slates for non-3D slides
    bg_3 = prod_dir / "3_closeup_details.png"
    bg_4 = prod_dir / "4_flat_wrap_preview.png"
    bg_7 = prod_dir / "7_color_paletter_overview.png"
    bg_8 = prod_dir / "8_size_guide.png"
    bg_10 = prod_dir / "10_thankyou.png"
    bg_11 = prod_dir / "15_flat_bundle_preview.png"

    # Slide 1 assets
    hero_dir = prod_dir / "1_hero_image"
    hero_base = hero_dir / "hero_image.png"
    hero_masks = [
        hero_dir / "hero_image_left_mask.png",
        hero_dir / "hero_image_middle_mask.png",
        hero_dir / "hero_image_right_mask.png",
    ]
    hero_disps = [
        hero_dir / "hero_image_displacement_left.png",
        hero_dir / "hero_image_displacement_middle.png",
        hero_dir / "hero_image_displacment_right.png",
    ]
    hero_glass = hero_dir / "hero_image_glass_layer.png"
    
    # Slides 2 and 9 assets
    bg_15 = prod_dir / "2_bundle_preview_blank_slate.png"
    bg_5 = prod_dir / "9_multiple_tumbler_display_blank_slate.png"
    
    prod_single_dir = prod_dir / "single_tumbler"
    prod_single_base = prod_single_dir / "single_tumbler.png"
    prod_single_mask = prod_single_dir / "single_tumbler_mask.png"
    prod_single_disp = prod_single_dir / "single_tumbler_displacement_map.png"
    prod_single_glass = prod_single_dir / "single_tumbler_glass_layer.png"

    # Slide 5 assets
    cat_dir = prod_dir / "5_lifestyle_mockup"
    cat_base = cat_dir / "5_lifestyle_mockup.png"
    cat_mask = cat_dir / "5_lifestyle_mockup_mask.png"
    cat_disp = cat_dir / "5_lifestyle_mockup_displacment_map.png"
    cat_glass = cat_dir / "5_lifestyle_mockup_glass_layer.png"

    # Slide 6 assets
    info_dir = prod_dir / "6_what_you_get_tumbler"
    info_base = info_dir / "6_what_you_get_tumbler.png"
    info_mask = info_dir / "6_what_you_get_tumbler_mask.png"
    info_disp = info_dir / "6_what_you_get_tumbler_displacement_map.png"
    info_glass = info_dir / "6_what_you_get_tumbler_glass_layer.png"

    triple_base = MOCKUP_DIR / "base_triple_tumbler_mockup.png"
    triple_masks = [
        MOCKUP_DIR / "base_triple_tumbler_mockup_mask_left.png",
        MOCKUP_DIR / "base_triple_tumbler_mockup_mask_center.png",
        MOCKUP_DIR / "base_triple_tumbler_mockup_mask_right.png",
    ]
    triple_disps = [
        MOCKUP_DIR / "base_triple_tumbler_mockup_displacement_left.png",
        MOCKUP_DIR / "base_triple_tumbler_mockup_displacement_center.png",
        MOCKUP_DIR / "base_triple_tumbler_mockup_displacement_right.png",
    ]

    saved = []

    selector = WrapSelector(wraps)

    # --- SLIDE 01: Hero ---
    hero_wraps = selector.get("_1", 3)
    if hero_base.exists():
        img = slide_01_hero(
            wrap_paths=hero_wraps,
            base_path=hero_base,
            mask_paths=hero_masks,
            disp_paths=hero_disps,
            glass_path=hero_glass,
            bundle_name=bundle_name,
            subtitle=subtitle,
            tags=tags,
            count=wrap_count,
            tumbler_type=meta.get("tumbler_type", "20oz Skinny Tumbler"),
        )
        saved.append(_save_slide(img, out_dir, "01_hero.png"))

    # --- SLIDE 02: Bundle Grid ---
    img = slide_02_bundle_grid(wraps, bg_15, prod_single_base, prod_single_mask, prod_single_disp, prod_single_glass)
    saved.append(_save_slide(img, out_dir, "02_bundle_grid.png"))

    # --- SLIDE 03: Close-Up ---
    closeup_wraps = selector.get("_3", 1)
    if bg_3.exists():
        img = slide_03_closeup(closeup_wraps, bg_3)
        saved.append(_save_slide(img, out_dir, "03_closeup_detail.png"))

    # --- SLIDE 04: Flat Wrap ---
    flat_wraps = selector.get("_4", 1)
    if bg_4.exists():
        img = slide_04_flat_wrap(flat_wraps[0], bg_4)
        saved.append(_save_slide(img, out_dir, "04_flat_wrap.png"))

    # --- SLIDE 05: Lifestyle ---
    lifestyle_wraps = selector.get("_5", 1)
    if cat_base.exists():
        img = slide_05_lifestyle(
            wrap_path=lifestyle_wraps[0],
            base_path=cat_base,
            mask_path=cat_mask,
            disp_path=cat_disp,
            glass_path=cat_glass,
        )
        saved.append(_save_slide(img, out_dir, "05_lifestyle_mockup.png"))

    # --- SLIDE 06: What You Get ---
    info_wraps = selector.get("_6", 1)
    if info_base.exists():
        img = slide_06_what_you_get(
            wrap_path=info_wraps[0],
            base_path=info_base,
            mask_path=info_mask,
            disp_path=info_disp,
            glass_path=info_glass,
        )
        saved.append(_save_slide(img, out_dir, "06_what_you_get.png"))

    # --- SLIDE 09: Multi Tumbler ---
    # Multi tumbler takes 4 images
    multi_wraps = selector.get("_9", 4)
    if bg_5.exists():
        img = slide_09_multi_tumbler(
            wrap_paths=multi_wraps,
            bg_path=bg_5,
            single_base=prod_single_base,
            single_mask=prod_single_mask,
            single_disp=prod_single_disp,
            single_glass=prod_single_glass,
        )
        saved.append(_save_slide(img, out_dir, "09_multi_tumbler.png"))

    # --- SLIDE 07: Color Palette ---
    if bg_7.exists():
        img = slide_07_color_palette(wraps, bg_7, palette_override=palette_override)
        saved.append(_save_slide(img, out_dir, "07_color_palette.png"))

    # --- SLIDE 08: Size Guide ---
    size_wraps = selector.get("_8", 1)
    if bg_8.exists():
        img = slide_08_size_guide(size_wraps[0], bg_8)
        saved.append(_save_slide(img, out_dir, "08_size_guide.png"))


    # --- SLIDE 10: Thank You ---
    if bg_10.exists():
        img = slide_10_thank_you(shop_name, shop_tagline, bg_10)
        saved.append(_save_slide(img, out_dir, "10_thank_you.png"))

    # --- SLIDE 11: Flat Bundle Preview ---
    if bg_11.exists():
        img = slide_11_flat_bundle_preview(wraps, bg_11)
        saved.append(_save_slide(img, out_dir, "11_flat_bundle_preview.png"))

    logger.info("-" * 60)
    logger.info("LISTING ENGINE: Generated %d slides -> %s", len(saved), out_dir)
    logger.info("-" * 60)

    # --- AI: Etsy listing copy (title / description / tags) ---
    generate_listing_copy(bundle_dir, meta)

    return saved
