"""
AI Listing Copy Generator
─────────────────────────
Generates Etsy-optimised title, description, and 13 tags for a bundle.

Supports Claude (Anthropic), Gemini (Google), and OpenAI.
Active provider and model are set in config.py.

Usage:
    from listing_engine.ai_listing import generate_listing_copy
    generate_listing_copy(bundle_dir, meta)
"""

import json
import logging
from pathlib import Path

from config import AI_LISTING_ENABLED, AI_PROVIDER, AI_MODELS, AI_API_KEYS

logger = logging.getLogger("etsy_tumbler")


# ──────────────────────────────────────────────────────────────
# Prompt builder
# ──────────────────────────────────────────────────────────────

def _build_prompt(meta: dict) -> str:
    bundle_name   = meta.get("bundle_name", "Collection")
    wrap_count    = meta.get("wrap_count", 15)
    aesthetic     = ", ".join(meta.get("aesthetic_tags", ["gothic", "dark fantasy"]))
    tumbler_type  = meta.get("tumbler_type", "20oz Skinny Tumbler")
    shop_name     = meta.get("shop_name", "")

    return f"""You are an expert Etsy SEO copywriter specialising in digital download products.

Create listing copy for the following digital product:

Product: {wrap_count}-piece tumbler wrap bundle
Collection name: {bundle_name}
Aesthetic / style keywords: {aesthetic}
Tumbler type: {tumbler_type}
Shop: {shop_name}

Requirements — return ONLY valid JSON, no markdown, no extra text:

{{
  "title": "<Etsy title, max 140 chars, front-load top keywords, no ALL-CAPS>",
  "description": "<Full Etsy description 150-200 words. Use relevant emojis. Sections: hook, what's included, file details, how to use, shop blurb. Selling points: straight + tapered formats included, 300 DPI, print-ready, instant digital download, commercial use.>",
  "tags": ["<tag1>", "<tag2>", ..., "<tag13>"]
}}

Tag rules:
- Exactly 13 tags
- Each tag max 20 characters (Etsy limit)
- Multi-word tags count as one tag (e.g. "gothic tumbler wrap")
- Mix broad (tumbler wrap) and niche ({bundle_name.lower()}) tags
- Include: tumbler wrap, digital download, skinny tumbler, 20oz tumbler
"""


# ──────────────────────────────────────────────────────────────
# Provider adapters
# ──────────────────────────────────────────────────────────────

def _call_claude(prompt: str, model: str, api_key: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _call_gemini(prompt: str, model: str, api_key: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    m = genai.GenerativeModel(model)
    response = m.generate_content(prompt)
    return response.text


def _call_openai(prompt: str, model: str, api_key: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return resp.choices[0].message.content


_PROVIDERS = {
    "claude": _call_claude,
    "gemini": _call_gemini,
    "openai": _call_openai,
}


# ──────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────

def generate_listing_copy(bundle_dir: Path, meta: dict) -> Path | None:
    """
    Call the configured AI provider and write listing copy to
    output/<bundle>/listing_copy.json and listing_copy.txt.

    Returns the path to listing_copy.json, or None on failure.
    """
    if not AI_LISTING_ENABLED:
        logger.info("  [AI] Listing copy disabled (AI_LISTING_ENABLED=False in config.py)")
        return None

    provider = AI_PROVIDER.lower()
    api_key  = AI_API_KEYS.get(provider, "")
    model    = AI_MODELS.get(provider, "")

    if not api_key:
        logger.warning(
            "  [AI] Skipped — no API key for provider '%s'. "
            "Add it to AI_API_KEYS in config.py.",
            provider,
        )
        return None

    if provider not in _PROVIDERS:
        logger.error("  [AI] Unknown provider '%s'. Choose claude / gemini / openai.", provider)
        return None

    prompt = _build_prompt(meta)
    logger.info("  [AI] Generating listing copy via %s (%s)…", provider, model)

    try:
        raw = _PROVIDERS[provider](prompt, model, api_key)
    except Exception as e:
        logger.error("  [AI] API call failed: %s", e)
        return None

    # Strip optional markdown fences
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error("  [AI] Could not parse JSON response: %s\nRaw:\n%s", e, raw[:400])
        return None

    # Validate
    title = str(data.get("title", ""))[:140]
    description = str(data.get("description", ""))
    tags = [str(t)[:20] for t in data.get("tags", [])][:13]

    if not title or not description or len(tags) < 5:
        logger.error("  [AI] Response incomplete — title=%r tags=%d", title[:40], len(tags))
        return None

    out_dir = bundle_dir.parent.parent / "output" / bundle_dir.name / "listing_images"
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON — machine-readable
    json_path = out_dir.parent / "listing_copy.json"
    json_path.write_text(
        json.dumps({"title": title, "description": description, "tags": tags}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # TXT — human-readable for quick copy-paste into Etsy
    txt_lines = [
        "═" * 60,
        "ETSY LISTING COPY",
        "═" * 60,
        "",
        "── TITLE ──────────────────────────────────────────────",
        title,
        f"({len(title)}/140 chars)",
        "",
        "── DESCRIPTION ─────────────────────────────────────────",
        description,
        "",
        "── TAGS (13) ───────────────────────────────────────────",
        "\n".join(f"  {i+1:2d}. {t}" for i, t in enumerate(tags)),
        "",
        "═" * 60,
    ]
    txt_path = out_dir.parent / "listing_copy.txt"
    txt_path.write_text("\n".join(txt_lines), encoding="utf-8")

    logger.info("  [AI] Saved → %s", json_path.name)
    logger.info("  [AI] Saved → %s", txt_path.name)
    return json_path
