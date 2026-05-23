"""Create a test bundle with sample artwork for pipeline testing."""
import os
import json
import random

from PIL import Image, ImageDraw

random.seed(42)

BUNDLE_DIR = "input/test_moon_bundle"
WRAPS_DIR = os.path.join(BUNDLE_DIR, "wraps")
os.makedirs(WRAPS_DIR, exist_ok=True)

COLORS = [
    (10, 14, 42),
    (45, 27, 78),
    (201, 168, 76),
    (184, 184, 192),
    (139, 58, 74),
    (26, 26, 26),
]

# Create 5 test wrap images
for i in range(5):
    img = Image.new("RGB", (3000, 3000), COLORS[i % len(COLORS)])
    draw = ImageDraw.Draw(img)
    for j in range(20):
        x1 = random.randint(0, 2500)
        y1 = random.randint(0, 2500)
        x2 = x1 + random.randint(100, 500)
        y2 = y1 + random.randint(100, 500)
        color = COLORS[(i + j) % len(COLORS)]
        draw.ellipse([(x1, y1), (x2, y2)], fill=color)
    
    filename = f"moon_design_{i+1:02d}.png"
    img.save(os.path.join(WRAPS_DIR, filename))
    print(f"Created {filename}")

# Create bundle.json
meta = {
    "bundle_name": "Moon Ritual",
    "subtitle": "5 Tumbler Wrap Bundle",
    "wrap_count": 5,
    "aesthetic_tags": ["Dark", "Celestial", "Mystic", "Timeless"],
    "shop_name": "xfantasypro",
    "shop_tagline": "Premium Digital Designs",
}

with open(os.path.join(BUNDLE_DIR, "bundle.json"), "w") as f:
    json.dump(meta, f, indent=2)

print("bundle.json created")
print("Test bundle ready!")
