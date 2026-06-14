"""
Pinterest AI Marketing Copy Generator
─────────────────────────────────────
Generates Pinterest-optimized title, description, tags, and 5 hooks.
"""

import json
import logging
from pathlib import Path

from config import PINTEREST_USE_AI_COPY, AI_API_KEYS

logger = logging.getLogger("etsy_tumbler")

def generate_pinterest_copy(bundle_dir: Path, bundle_name: str) -> dict | None:
    """
    Call Gemini to generate Pinterest copy. Returns a dict with:
    {
        "title": "...",
        "description": "...",
        "tags": ["..."],
        "hooks": ["hook1", "hook2", "hook3", "hook4", "hook5"]
    }
    If API fails or is disabled, returns None.
    """
    if not PINTEREST_USE_AI_COPY:
        logger.info("  [Pinterest AI] AI copy disabled (PINTEREST_USE_AI_COPY=False)")
        return None

    api_key = AI_API_KEYS.get("gemini", "")
    if not api_key:
        logger.warning("  [Pinterest AI] No Gemini API key found. Using static text.")
        return None

    prompt = f"""You are an expert Pinterest SEO copywriter and marketer.
I need marketing copy for a digital product: a '{bundle_name}' tumbler wrap bundle.

Requirements — return ONLY valid JSON, no markdown, no extra text:
{{
  "title": "<Pinterest title, max 100 chars>",
  "description": "<Pinterest description, max 500 chars, include call to action>",
  "tags": ["<tag1>", "<tag2>", "<tag3>", "<tag4>", "<tag5>"],
  "hooks": [
    "<Short punchy hook 1 for text overlay, max 5 words>",
    "<Short punchy hook 2 for text overlay, max 5 words>",
    "<Short punchy hook 3 for text overlay, max 5 words>",
    "<Short punchy hook 4 for text overlay, max 5 words>",
    "<Short punchy hook 5 for text overlay, max 5 words>"
  ]
}}
"""

    logger.info("  [Pinterest AI] Generating hooks and SEO copy via Gemini...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        # Using gemini-2.5-flash for fast text generation
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Strip optional markdown fences
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            
        data = json.loads(text)
        
        # Validate structure
        if "title" not in data or "hooks" not in data or len(data["hooks"]) < 5:
            raise ValueError("Incomplete JSON response from AI.")
            
        # Save machine-readable and human-readable versions
        out_dir = bundle_dir.parent.parent / "output" / bundle_dir.name / "pinterest"
        out_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = out_dir / "pinterest_copy.json"
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        
        txt_lines = [
            "═" * 60,
            "PINTEREST COPY",
            "═" * 60,
            "",
            "── TITLE ──────────────────────────────────────────────",
            data["title"],
            "",
            "── DESCRIPTION ─────────────────────────────────────────",
            data["description"],
            "",
            "── TAGS ────────────────────────────────────────────────",
            " ".join(f"#{t.replace(' ', '')}" for t in data["tags"]),
            "",
            "── TEXT OVERLAY HOOKS ──────────────────────────────────",
        ]
        for i, hook in enumerate(data["hooks"]):
            txt_lines.append(f"  {i+1}. {hook}")
            
        txt_path = out_dir / "pinterest_copy.txt"
        txt_path.write_text("\n".join(txt_lines), encoding="utf-8")
        
        logger.info("  [Pinterest AI] Saved → pinterest_copy.txt")
        return data

    except Exception as e:
        logger.error("  [Pinterest AI] API call failed: %s", e)
        return None
