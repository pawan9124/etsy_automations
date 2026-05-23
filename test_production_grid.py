import logging
from pathlib import Path
from listing_engine.slides import slide_02_bundle_grid, slide_09_multi_tumbler

logging.basicConfig(level=logging.INFO)

# Define paths
PROD_DIR = Path("D:/Ai-Repos/etsy_automations/mockup_assets/tumblers_production")
SINGLE_DIR = PROD_DIR / "single_tumbler"

bg_15 = PROD_DIR / "2_bundle_preview_blank_slate.png"
bg_5 = PROD_DIR / "9_multiple_tumbler_display_blank_slate.png"

single_mask = SINGLE_DIR / "single_tumbler_mask.png"
single_disp = SINGLE_DIR / "single_tumbler_displacement_map.png"
single_glass = SINGLE_DIR / "single_tumbler_glass_layer.png"

wrap_dir = Path("D:/Ai-Repos/etsy_automations/input/eternal-moon")
wraps = sorted([p for p in wrap_dir.glob("*.png")])

if len(wraps) < 15:
    # pad with duplicates if somehow less than 15
    wraps = (wraps * (15 // len(wraps) + 1))[:15]

# Test Slide 2
print("Generating Slide 2 (15 Grid)...")
slide2 = slide_02_bundle_grid(wraps, bg_15, single_mask, single_disp, single_glass)
slide2_out = Path("D:/Ai-Repos/etsy_automations/test_slide2_grid.png")
slide2.save(slide2_out)
print(f"Saved {slide2_out}")

# Test Slide 9
print("Generating Slide 9 (5 Row)...")
slide9 = slide_09_multi_tumbler(wraps, bg_5, single_mask, single_disp, single_glass)
slide9_out = Path("D:/Ai-Repos/etsy_automations/test_slide9_row.png")
slide9.save(slide9_out)
print(f"Saved {slide9_out}")
