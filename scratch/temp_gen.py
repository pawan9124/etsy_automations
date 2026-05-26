import sys
sys.path.append('.')
from pathlib import Path
from listing_engine.generator import _collect_wraps, _load_bundle_meta
from listing_engine.slides import slide_01_b_hero_single_wrap
from config import OUTPUT_DIR

MOCKUP_DIR = Path('mockup_assets')
bundle_dir = OUTPUT_DIR / 'Gothic Cowgirl Tumbler Wrap'
wraps = _collect_wraps(bundle_dir)
meta = _load_bundle_meta(bundle_dir)

prod_dir = MOCKUP_DIR / "tumblers_production"
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

out_dir = bundle_dir / "listing_images"
out_dir.mkdir(parents=True, exist_ok=True)

print("Generating single wrap hero...")
img_b = slide_01_b_hero_single_wrap(
    wrap_path=wraps[0],
    base_path=hero_base,
    mask_paths=hero_masks,
    disp_paths=hero_disps,
    glass_path=hero_glass,
    bundle_name=meta["bundle_name"],
    subtitle=meta["subtitle"],
    tags=meta.get("aesthetic_tags", []),
)
out_path = out_dir / "01_1_hero_single_wrap.png"
img_b.save(out_path, format="PNG", dpi=(300, 300), compress_level=1)
print(f"Saved to {out_path}")
