import cv2
import numpy as np
from PIL import Image, ImageChops
from pathlib import Path

# File paths
test_dir = Path(r"D:\Ai-Repos\etsy_automations\mockup_assets\testing")
base_path = test_dir / "original_mockup.png"
mask_path = test_dir / "mask_tum.png"
disp_path = test_dir / "displacement_map.png"
glass_path = test_dir / "glass_layer.png"

# Test wrap
wrap_path = Path(r"D:\Ai-Repos\etsy_automations\input\eternal-moon\eternal-moon (1).png")
import cv2
import numpy as np
from PIL import Image, ImageChops
from pathlib import Path

# File paths
test_dir = Path(r"D:\Ai-Repos\etsy_automations\mockup_assets\testing")
base_path = test_dir / "original_mockup.png"
mask_path = test_dir / "mask_tum.png"
disp_path = test_dir / "displacement_map.png"
glass_path = test_dir / "glass_layer.png"

# Test wrap
wrap_path = Path(r"D:\Ai-Repos\etsy_automations\input\eternal-moon\eternal-moon (1).png")

print("Loading images...")
base = Image.open(base_path).convert("RGBA")
wrap = Image.open(wrap_path).convert("RGBA")
mask = Image.open(mask_path).convert("L")
disp = Image.open(disp_path).convert("L")
glass = Image.open(glass_path).convert("RGBA")

# Resize assets to match base size
mask = mask.resize(base.size, Image.Resampling.LANCZOS)
disp = disp.resize(base.size, Image.Resampling.LANCZOS)
glass = glass.resize(base.size, Image.Resampling.LANCZOS)

# 1. Resize wrap to mask bounding box
mask_bbox = mask.getbbox()
target_w = mask_bbox[2] - mask_bbox[0]
target_h = mask_bbox[3] - mask_bbox[1]

aspect_ratio = wrap.width / wrap.height
new_h = target_h
new_w = int(new_h * aspect_ratio)
resized_wrap = wrap.resize((new_w, new_h), Image.Resampling.LANCZOS)

# Create full canvas for the wrap
canvas = Image.new("RGBA", base.size, (0, 0, 0, 0))
paste_x = mask_bbox[0] + (target_w - new_w) // 2
paste_y = mask_bbox[1]
canvas.paste(resized_wrap, (paste_x, paste_y))

# 2. Apply cv2.remap displacement
print("Applying 3D displacement...")
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

# 3. Composite design onto base
result = base.copy()
result.paste(warped_pil, (0, 0), mask)

# 4. Composite glass overlay using Screen blend mode
print("Applying perfect glass overlay (Screen blend)...")
# Since the glass is black & white, Screen blend will turn black to transparent
screened_result = ImageChops.screen(result, glass)

# Let's output three versions with different opacities so you can choose the best one!
opacities = [1.0, 0.75, 0.50]

for opacity in opacities:
    # Blend the screened result with the original result based on opacity
    final_opacity_result = Image.blend(result, screened_result, opacity)
    
    # Save result
    opacity_str = int(opacity * 100)
    output_path = test_dir / f"test_result_glass_opacity_{opacity_str}.png"
    final_opacity_result.save(output_path)
    print(f"Saved: {output_path}")

print("Done testing opacities!")
