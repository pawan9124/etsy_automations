import cv2
import numpy as np
from PIL import Image, ImageChops
from pathlib import Path

# File paths
test_dir = Path(r"D:\Ai-Repos\etsy_automations\mockup_assets\three_tumbler")
base_path = test_dir / "three_tumbler.png"
glass_path = test_dir / "three_tumbler_glass_layer.png"

masks = {
    "left": test_dir / "three_tumbler_left_mask.png",
    "middle": test_dir / "three_tumbler_middle_mask.png",
    "right": test_dir / "three_tumbler_right_mask.png"
}

displacements = {
    "left": test_dir / "three_tumbler_displacement_left.png",
    "middle": test_dir / "three_tumbler_displacement_middle.png",
    "right": test_dir / "three_tumbler_displacment_right.png"
}

# Test wrap
wrap_path = Path(r"D:\Ai-Repos\etsy_automations\input\eternal-moon\eternal-moon (1).png")

print("Loading images...")
base = Image.open(base_path).convert("RGBA")
wrap = Image.open(wrap_path).convert("RGBA")
glass = Image.open(glass_path).convert("RGBA")
glass = glass.resize(base.size, Image.Resampling.LANCZOS)

result = base.copy()

# Process each tumbler
tumblers = ["left", "middle", "right"]

for t in tumblers:
    print(f"Processing {t} tumbler...")
    mask = Image.open(masks[t]).convert("L")
    disp = Image.open(displacements[t]).convert("L")
    
    mask = mask.resize(base.size, Image.Resampling.LANCZOS)
    disp = disp.resize(base.size, Image.Resampling.LANCZOS)
    
    mask_bbox = mask.getbbox()
    if not mask_bbox:
        print(f"Warning: Mask for {t} is empty!")
        continue
        
    target_w = mask_bbox[2] - mask_bbox[0]
    target_h = mask_bbox[3] - mask_bbox[1]
    
    # Calculate crop for this tumbler (overlapping views of the full wrap)
    # Left shows left half (0 to 50%)
    # Middle shows center half (25% to 75%)
    # Right shows right half (50% to 100%)
    w_width, w_height = wrap.size
    
    if t == "left":
        crop_box = (0, 0, w_width // 2, w_height)
    elif t == "middle":
        crop_box = (w_width // 4, 0, 3 * w_width // 4, w_height)
    else: # right
        crop_box = (w_width // 2, 0, w_width, w_height)
        
    wrap_crop = wrap.crop(crop_box)
    
    # Resize crop to fit the mask
    resized_wrap = wrap_crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # Paste onto a full canvas
    canvas = Image.new("RGBA", base.size, (0, 0, 0, 0))
    canvas.paste(resized_wrap, (mask_bbox[0], mask_bbox[1]))
    
    # Warp with displacement map
    design_cv = cv2.cvtColor(np.array(canvas), cv2.COLOR_RGBA2BGRA)
    disp_cv = np.array(disp, dtype=np.int16)
    h, w = disp_cv.shape[:2]
    
    yy, xx = np.mgrid[0:h, 0:w]
    map_y = yy.astype(np.float32)
    map_x = xx.astype(np.float32)
    
    strength = 40
    offset = (disp_cv.astype(np.float32) - 128.0) / 128.0
    map_x += offset * strength
    
    warped_cv = cv2.remap(
        design_cv, map_x, map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0)
    )
    warped_pil = Image.fromarray(cv2.cvtColor(warped_cv, cv2.COLOR_BGRA2RGBA))
    
    # Composite onto result
    result.paste(warped_pil, (0, 0), mask)

print("Applying glass overlay to all three tumblers...")
screened_result = ImageChops.screen(result, glass)
# Use the proven 75% opacity
final_result = Image.blend(result, screened_result, 0.75)

output_path = test_dir / "three_tumbler_test_result.png"
final_result.save(output_path)
print(f"Done! Saved to {output_path}")
