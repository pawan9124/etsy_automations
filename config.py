"""
Configuration for Etsy Tumbler Wrap Automation — Phase 1
All dimensions, paths, and settings in one place.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Base Paths ───────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
TEMPLATES_DIR = BASE_DIR / "templates"
SCRIPTS_DIR = BASE_DIR / "scripts"

# ─── Image Settings ──────────────────────────────────────────
DPI = 300
OUTPUT_FORMAT = "PNG"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

# Minimum source resolution (pixels) — reject anything smaller
MIN_WIDTH_PX = 2000
MIN_HEIGHT_PX = 2000

# Resampling filter (Lanczos is the highest-quality downscale filter in Pillow)
RESAMPLE_FILTER = "LANCZOS"

# ─── Resize Strategy ─────────────────────────────────────────
# How artwork is fitted into the tumbler wrap dimensions:
#   "stretch" → Stretch to exact target size (what Photoshop does, ~6% unnoticeable)
#   "cover"   → Scale to COVER the target, centre-crop (may clip edges)
#   "contain" → Scale to FIT entirely + blurred edge extension (zero clipping)
#   "fit"     → Scale to FIT entirely, pad with black (no clipping, but visible bars)
RESIZE_MODE = "stretch"

# ─── 20 oz Straight Tumbler Wrap ─────────────────────────────
STRAIGHT_WIDTH_IN = 9.3      # inches (circumference)
STRAIGHT_HEIGHT_IN = 8.2     # inches

STRAIGHT_WIDTH_PX = int(STRAIGHT_WIDTH_IN * DPI)   # 2790
STRAIGHT_HEIGHT_PX = int(STRAIGHT_HEIGHT_IN * DPI)  # 2460

# ─── 20 oz Tapered Tumbler Wrap ──────────────────────────────
# Common 20 oz tapered skinny tumbler measurements:
#   Top circumference ≈ 9.45"   Bottom circumference ≈ 8.65"
# Output is a trapezoid (wider top, narrower bottom) on transparent canvas.
TAPERED_TOP_WIDTH_IN = 9.45
TAPERED_BOTTOM_WIDTH_IN = 8.65
TAPERED_HEIGHT_IN = 8.25

# Canvas matches the top (widest) circumference
TAPERED_WIDTH_PX = int(TAPERED_TOP_WIDTH_IN * DPI)          # 2835
TAPERED_HEIGHT_PX = int(TAPERED_HEIGHT_IN * DPI)             # 2475
TAPERED_BOTTOM_WIDTH_PX = int(TAPERED_BOTTOM_WIDTH_IN * DPI) # 2595

# ─── Naming ──────────────────────────────────────────────────
STRAIGHT_SUFFIX = "_straight"
TAPERED_SUFFIX = "_tapered"

# ─── Logging ─────────────────────────────────────────────────
LOG_FILENAME = "processing.log"
LOG_LEVEL = "INFO"



# Path to your OAuth2 credentials JSON downloaded from Google Cloud Console.
# Steps to get it: https://developers.google.com/drive/api/quickstart/python
DRIVE_CREDENTIALS_FILE = BASE_DIR / "credentials" / "google_credentials.json"

# Token is auto-created after first browser auth — do not edit manually
DRIVE_TOKEN_FILE = BASE_DIR / "credentials" / "google_token.json"

# ID of the parent folder in your Drive where bundle folders will be created.
# Open the folder in Drive → copy the ID from the URL:
#   https://drive.google.com/drive/folders/<THIS_IS_THE_ID>
DRIVE_PARENT_FOLDER_ID = "1wVgpGEIkmORDVFw7_f_T0T60slCgr8Do"

# ================ FLAG SETUP ============================
# ─── Google Drive Upload ─────────────────────────────────────
# Set to False to skip Drive upload entirely
DRIVE_UPLOAD_ENABLED = True
# ─── Marketing Video ──────────────────────────────────────────
# Set to False to skip generating the 360° marketing presentation mp4
VIDEO_GENERATION_ENABLED = True

# ─── Pinterest Marketing ──────────────────────────────────────
# Generate 5 vertical (9:16) pins for Pinterest (1 video + 4 images)
PINTEREST_MARKETING_ENABLED = True
# Automatically generate Pinterest SEO copy and hooks using AI
PINTEREST_USE_AI_COPY = True
PINTEREST_W = 1080
PINTEREST_H = 1920

# ─── AI Focal Detection ───────────────────────────────────────
# Set to True to use Gemma 4 for intelligent focal point detection
AI_FOCAL_DETECTION_ENABLED = False
# Fallback method if API fails: "heuristic" or "opencv"
FOCAL_DETECTION_FALLBACK = "heuristic"

# Which slides should trigger an AI focal detection API call? 
# (If a wrap was already analyzed, its cached result is always used regardless of this list)
AI_FOCAL_SLIDES = [
    "slide_01_hero",
    "slide_01_b_hero_single_wrap",
    "slide_02_bundle_grid",
    "slide_05_lifestyle",
    "slide_06_what_you_get",
    "slide_09_multi_tumbler"
]

# ─── AI Listing Copy ──────────────────────────────────────────
# Set to False to skip AI copy generation entirely
AI_LISTING_ENABLED = False

# Provider: "claude" | "gemini" | "openai"
AI_PROVIDER = "claude"

# Model names per provider — change here when you switch
AI_MODELS = {
    "claude": "claude-sonnet-4-6",
    "gemini": "gemini-2.0-flash",
    "openai": "gpt-4o",
}

# API keys — set the one matching your active provider.
# Leave others as empty string "".
AI_API_KEYS = {
    "claude": os.getenv("CLAUDE_API_KEY", ""),   # paste your Anthropic key here or in .env
    "gemini": os.getenv("GEMINI_API_KEY", ""),   # paste your Google AI key here or in .env
    "openai": os.getenv("OPENAI_API_KEY", ""),   # paste your OpenAI key here or in .env
}
