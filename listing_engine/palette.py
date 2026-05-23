"""
Color Palette Extraction — K-means clustering on bundle artwork.

Extracts the N most dominant colors from a set of images using
a lightweight pure-NumPy K-means implementation (no sklearn needed).
"""

import logging
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger("etsy_tumbler")

# Nearest CSS color names for labeling
_CSS_COLORS = {
    "Ivory":        (255, 255, 240),
    "Snow White":   (255, 250, 250),
    "Antique White":(250, 235, 215),
    "Champagne":    (247, 231, 206),
    "Gold":         (255, 215, 0),
    "Amber":        (255, 191, 0),
    "Copper":       (184, 115, 51),
    "Bronze":       (205, 127, 50),
    "Rose Gold":    (183, 110, 121),
    "Blush":        (222, 165, 164),
    "Coral":        (255, 127, 80),
    "Salmon":       (250, 128, 114),
    "Crimson":      (220, 20, 60),
    "Ruby":         (155, 17, 30),
    "Burgundy":     (128, 0, 32),
    "Maroon":       (128, 0, 0),
    "Rose":         (255, 0, 127),
    "Magenta":      (255, 0, 255),
    "Plum":         (142, 69, 133),
    "Violet":       (127, 0, 255),
    "Lavender":     (230, 230, 250),
    "Purple":       (128, 0, 128),
    "Royal Purple": (120, 81, 169),
    "Indigo":       (75, 0, 130),
    "Deep Navy":    (10, 14, 42),
    "Navy":         (0, 0, 128),
    "Cobalt":       (0, 71, 171),
    "Royal Blue":   (65, 105, 225),
    "Sky Blue":     (135, 206, 235),
    "Cyan":         (0, 255, 255),
    "Teal":         (0, 128, 128),
    "Emerald":      (80, 200, 120),
    "Forest Green": (34, 139, 34),
    "Sage":         (188, 184, 138),
    "Olive":        (128, 128, 0),
    "Moss":         (138, 154, 91),
    "Midnight":     (25, 25, 60),
    "Obsidian":     (20, 20, 20),
    "Charcoal":     (54, 69, 79),
    "Slate":        (112, 128, 144),
    "Silver":       (192, 192, 192),
    "Pearl":        (234, 224, 200),
    "Smoke":        (96, 96, 96),
    "Graphite":     (63, 63, 63),
    "Jet Black":    (10, 10, 10),
    "Onyx":         (30, 30, 30),
    "Ash":          (178, 190, 181),
    "Cream":        (255, 253, 208),
    "Caramel":      (255, 211, 140),
    "Rust":         (183, 65, 14),
    "Terracotta":   (204, 78, 92),
    "Mahogany":     (192, 64, 0),
    "Sienna":       (160, 82, 45),
    "Chocolate":    (123, 63, 0),
    "Espresso":     (60, 30, 10),
    "Mocha":        (110, 70, 40),
    "Sand":         (194, 178, 128),
    "Tan":          (210, 180, 140),
    "Taupe":        (72, 60, 50),
    "Pewter":       (150, 150, 150),
    "Steel":        (113, 121, 126),
    "Ice Blue":     (153, 204, 255),
    "Turquoise":    (64, 224, 208),
    "Aqua":         (0, 128, 128),
    "Mint":         (189, 252, 201),
}


def _color_distance(c1, c2):
    """Euclidean distance between two RGB tuples."""
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5


def name_color(rgb: tuple[int, int, int]) -> str:
    """Find the closest named CSS color for an RGB tuple."""
    best_name = "Unknown"
    best_dist = float("inf")
    for name, ref in _CSS_COLORS.items():
        d = _color_distance(rgb, ref)
        if d < best_dist:
            best_dist = d
            best_name = name
    return best_name


def _kmeans(pixels: np.ndarray, k: int = 6, max_iter: int = 20) -> np.ndarray:
    """
    Simple K-means clustering on pixel data.
    Returns k centroids as (k, 3) array of RGB values.
    """
    # Random initial centroids
    rng = np.random.default_rng(42)
    indices = rng.choice(len(pixels), size=k, replace=False)
    centroids = pixels[indices].astype(np.float64)

    for _ in range(max_iter):
        # Assign each pixel to nearest centroid
        dists = np.linalg.norm(pixels[:, None] - centroids[None, :], axis=2)
        labels = np.argmin(dists, axis=1)

        # Update centroids
        new_centroids = np.array([
            pixels[labels == i].mean(axis=0) if (labels == i).any() else centroids[i]
            for i in range(k)
        ])

        if np.allclose(centroids, new_centroids, atol=1.0):
            break
        centroids = new_centroids

    return centroids.astype(np.uint8)


def extract_palette(
    image_paths: list[Path],
    n_colors: int = 6,
    sample_size: int = 5000,
) -> list[dict]:
    """
    Extract dominant colors from a set of images.

    Returns a list of dicts: [{"name": "Deep Navy", "hex": "#0a0e2a", "rgb": (10,14,42)}, ...]
    """
    all_pixels = []

    for p in image_paths:
        img = Image.open(p).convert("RGB")
        # Downsample for speed
        img_small = img.resize((100, 100), Image.Resampling.LANCZOS)
        pixels = np.array(img_small).reshape(-1, 3)
        all_pixels.append(pixels)

    combined = np.vstack(all_pixels)

    # Random sample if too many pixels
    if len(combined) > sample_size:
        rng = np.random.default_rng(42)
        indices = rng.choice(len(combined), size=sample_size, replace=False)
        combined = combined[indices]

    # Filter out near-black and near-white (often background/noise)
    brightness = combined.mean(axis=1)
    valid = (brightness > 15) & (brightness < 245)
    combined = combined[valid]

    centroids = _kmeans(combined, k=n_colors)

    # Sort by brightness (dark to light)
    order = centroids.mean(axis=1).argsort()
    centroids = centroids[order]

    palette = []
    for c in centroids:
        r, g, b = int(c[0]), int(c[1]), int(c[2])
        palette.append({
            "name": name_color((r, g, b)),
            "hex": f"#{r:02x}{g:02x}{b:02x}",
            "rgb": (r, g, b),
        })

    logger.info("  [PALETTE] Extracted %d colors from %d images", n_colors, len(image_paths))
    return palette
