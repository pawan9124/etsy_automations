import os
import shutil
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
import base64
import io
import sqlite3
from datetime import datetime

from listing_engine.slides import slide_01_hero, slide_01_b_hero_single_wrap, slide_03_closeup, slide_05_lifestyle

app = FastAPI(title="Etsy Mockup Teaser API")

@app.get("/api/health")
def health_check():
    return {"status": "awake"}

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SQLite Database Setup ---
DB_FILE = "leads.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            etsy_url TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class LeadData(BaseModel):
    name: str
    email: str
    etsyUrl: str

MOCKUP_DIR = Path("mockup_assets")
TEASER_TEMP_DIR = Path("input/teaser_temp")
TEASER_OUT_DIR = Path("output/teaser_temp")

@app.post("/api/generate-teaser")
async def generate_teaser(files: List[UploadFile] = File(...)):
    """
    Accepts 1 to 4 image uploads and generates a stunning 3D Hero image.
    Skips the heavy PDF/Video pipeline for a fast demo response.
    """
    # Clean up previous temp files
    if TEASER_TEMP_DIR.exists():
        shutil.rmtree(TEASER_TEMP_DIR)
    TEASER_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    if TEASER_OUT_DIR.exists():
        shutil.rmtree(TEASER_OUT_DIR)
    TEASER_OUT_DIR.mkdir(parents=True, exist_ok=True)

    wrap_paths = []
    # Save uploaded files
    for file in files[:4]:  # limit to 4 files
        file_path = TEASER_TEMP_DIR / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        wrap_paths.append(file_path)

    if not wrap_paths:
        return {"error": "No valid files uploaded"}

    # Load base assets
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

    # Default metadata for the teaser
    bundle_name = "Your Premium Bundle"
    subtitle = "Tumbler Wrap Collection"
    tags = ["Premium", "Trending", "High-Res"]

    out_image_path = TEASER_OUT_DIR / "teaser_hero.png"

    # Distribute uploaded files across the 3 custom mockups
    wrap1 = wrap_paths[0]
    wrap2 = wrap_paths[1] if len(wrap_paths) > 1 else wrap_paths[0]
    wrap3 = wrap_paths[2] if len(wrap_paths) > 2 else wrap1

    # Always use the first uploaded wrap for a 360 single wrap view to show off the 3D capability
    img = slide_01_b_hero_single_wrap(
        wrap_path=wrap1,
        base_path=hero_base,
        mask_paths=hero_masks,
        disp_paths=hero_disps,
        glass_path=hero_glass,
        bundle_name=bundle_name,
        subtitle=subtitle,
        tags=tags,
    )
    
    # Helper to convert PIL Image to Base64
    def image_to_base64(img_obj):
        buf = io.BytesIO()
        img_obj.save(buf, format="PNG", compress_level=1)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # 1. 360 Hero View
    hero_b64 = image_to_base64(img)

    # 2. Closeup Detail
    closeup_bg = prod_dir / "3_closeup_details.png"
    img_closeup = slide_03_closeup(wrap_paths=[wrap3], bg_path=closeup_bg)
    closeup_b64 = image_to_base64(img_closeup)

    # 3. Lifestyle Mockup
    life_dir = prod_dir / "5_lifestyle_mockup"
    img_lifestyle = slide_05_lifestyle(
        wrap_path=wrap2,
        base_path=life_dir / "5_lifestyle_mockup.png",
        mask_path=life_dir / "5_lifestyle_mockup_mask.png",
        disp_path=life_dir / "5_lifestyle_mockup_displacment_map.png",
        glass_path=life_dir / "5_lifestyle_mockup_glass_layer.png",
    )
    lifestyle_b64 = image_to_base64(img_lifestyle)

    # We still save hero for debugging locally, but we return all 3 as JSON
    img.save(out_image_path, format="PNG", dpi=(300, 300), compress_level=1)

    return JSONResponse({
        "hero": "data:image/png;base64," + hero_b64,
        "closeup": "data:image/png;base64," + closeup_b64,
        "lifestyle": "data:image/png;base64," + lifestyle_b64
    })

@app.post("/api/capture-lead")
async def capture_lead(lead: LeadData):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "INSERT INTO leads (name, email, etsy_url, timestamp) VALUES (?, ?, ?, ?)",
            (lead.name, lead.email, lead.etsyUrl, datetime.utcnow())
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Lead captured successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
