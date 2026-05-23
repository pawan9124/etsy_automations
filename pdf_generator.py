"""
PDF Download Instruction Generator
────────────────────────────────────
Creates download_instruction.pdf by placing the thank-you template image
as background and overlaying a clickable Drive link inside the empty box.

Output: output/<bundle>/download_instruction.pdf
"""

import logging
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

from config import OUTPUT_DIR

logger = logging.getLogger("etsy_tumbler")

TEMPLATE_PATH = Path(__file__).parent / "mockup_assets" / "tumblers_production" / "pdf_template_thankyou.png"

# ── Template image is 941 × 1672 px ────────────────────────────
# PDF page uses same aspect ratio at A4 width (595 pts)
_IMG_W, _IMG_H = 941, 1672
_SCALE = 595 / _IMG_W          # 0.6323
PAGE_W = 595
PAGE_H = round(_IMG_H * _SCALE)   # ≈ 1057 pts

# ── Empty box in template (measured in image px, from top-left) ─
# The black box (inside the gold ornate frame) for the link sits here:
_BOX_X1, _BOX_Y1 = 100, 648    # top-left corner (image pixels)
_BOX_X2, _BOX_Y2 = 840, 1153   # bottom-right corner


def _px_to_pdf(x_px: int, y_px: int):
    """
    Convert image-pixel coords (origin top-left) to
    ReportLab PDF coords (origin bottom-left).
    """
    return x_px * _SCALE, (PAGE_H - y_px * _SCALE)


def generate_download_pdf(bundle_name: str, drive_link: str) -> Path | None:
    """
    Build download_instruction.pdf for *bundle_name* using *drive_link*.
    Returns the PDF path, or None on failure.
    """
    if not drive_link:
        logger.warning("  [PDF] No Drive link provided — skipping PDF generation")
        return None

    if not TEMPLATE_PATH.exists():
        logger.error("  [PDF] Template not found: %s", TEMPLATE_PATH)
        return None

    out_dir = OUTPUT_DIR / bundle_name
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "download_instruction.pdf"

    # ── PDF canvas ───────────────────────────────────────────────
    c = canvas.Canvas(str(pdf_path), pagesize=(PAGE_W, PAGE_H))

    # 1) Full-page background image
    c.drawImage(
        ImageReader(str(TEMPLATE_PATH)),
        0, 0,
        width=PAGE_W, height=PAGE_H,
        preserveAspectRatio=False,
    )

    # 2) Compute box region in PDF coordinates
    box_left,   box_top    = _px_to_pdf(_BOX_X1, _BOX_Y1)
    box_right,  box_bottom = _px_to_pdf(_BOX_X2, _BOX_Y2)
    box_w  = box_right - box_left
    box_h  = box_top   - box_bottom   # top > bottom in PDF coords
    box_cx = box_left + box_w / 2
    box_cy = box_bottom + box_h / 2

    # 3) Center button + URL as a single block in the middle of the box
    btn_w, btn_h = box_w * 0.78, 54
    gap = 20  # space between button and URL line
    url_font_size = 9
    block_h = btn_h + gap + url_font_size

    # Top of the combined (button + URL) block, centered vertically in box
    block_top = box_cy + block_h / 2

    btn_x = box_cx - btn_w / 2
    btn_y = block_top - btn_h        # button top of block

    c.setFillColor(HexColor("#C9A84C"))       # antique gold
    c.roundRect(btn_x, btn_y, btn_w, btn_h, radius=8, fill=1, stroke=0)

    # 4) Button text
    c.setFillColor(HexColor("#0D0D0D"))       # near-black
    c.setFont("Helvetica-Bold", 14)
    btn_label = "CLICK HERE TO ACCESS YOUR COLLECTION"
    text_w = c.stringWidth(btn_label, "Helvetica-Bold", 14)
    c.drawString(box_cx - text_w / 2, btn_y + btn_h * 0.38, btn_label)

    # 5) URL displayed below button in small gold text
    c.setFont("Helvetica", url_font_size)
    c.setFillColor(HexColor("#C9A84C"))
    display_url = drive_link if len(drive_link) <= 70 else drive_link[:67] + "..."
    url_y = btn_y - gap
    c.drawString(box_cx - c.stringWidth(display_url, "Helvetica", url_font_size) / 2, url_y, display_url)

    # 6) Invisible clickable link covering the button
    link_pad = 4
    c.linkURL(
        drive_link,
        (btn_x - link_pad, btn_y - link_pad,
         btn_x + btn_w + link_pad, btn_y + btn_h + link_pad),
        relative=0,
    )

    c.save()
    logger.info("  [PDF] Saved → %s", pdf_path)
    return pdf_path
