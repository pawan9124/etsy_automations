"""
Configuration for Etsy Tumbler Wrap Automation — Phase 1
All dimensions, paths, and settings in one place.
"""

from pathlib import Path

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

# ─── Google Drive Upload ─────────────────────────────────────
# Set to False to skip Drive upload entirely
DRIVE_UPLOAD_ENABLED = True

# Path to your OAuth2 credentials JSON downloaded from Google Cloud Console.
# Steps to get it: https://developers.google.com/drive/api/quickstart/python
DRIVE_CREDENTIALS_FILE = BASE_DIR / "credentials" / "google_credentials.json"

# Token is auto-created after first browser auth — do not edit manually
DRIVE_TOKEN_FILE = BASE_DIR / "credentials" / "google_token.json"

# ID of the parent folder in your Drive where bundle folders will be created.
# Open the folder in Drive → copy the ID from the URL:
#   https://drive.google.com/drive/folders/<THIS_IS_THE_ID>
DRIVE_PARENT_FOLDER_ID = "1wVgpGEIkmORDVFw7_f_T0T60slCgr8Do"

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
    "claude": "",   # paste your Anthropic key here
    "gemini": "",   # paste your Google AI key here
    "openai": "",   # paste your OpenAI key here
}
