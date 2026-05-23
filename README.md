# 🎨 Etsy Tumbler Wrap Automation — Phase 1

Batch-process artwork PNGs into print-ready **20 oz tumbler wraps** (straight + tapered).

## Quick Start

```bash
# 1. Install dependency
pip install -r requirements.txt

# 2. Create a bundle folder and drop your artwork PNGs in
#    Example: input/eternal_moon_bundle/

# 3. Run
python main.py                       # all bundles
python main.py eternal_moon_bundle   # single bundle
```

## Folder Structure

```
etsy_automations/
├── input/                    ← Drop your artwork bundles here
│   └── eternal_moon_bundle/
│       ├── moon_ritual.png
│       └── lunar_phase.png
├── output/                   ← Processed wraps appear here
│   └── eternal_moon_bundle/
│       ├── straight_wraps/
│       │   ├── moon_ritual_01_straight.png
│       │   └── lunar_phase_02_straight.png
│       └── tapered_wraps/
│           ├── moon_ritual_01_tapered.png
│           └── lunar_phase_02_tapered.png
├── logs/                     ← Processing logs
├── templates/                ← (reserved for future phases)
├── scripts/                  ← (reserved for future phases)
├── config.py                 ← All settings in one place
├── utils.py                  ← Folder / logging / validation helpers
├── processor.py              ← Core image processing logic
├── main.py                   ← Entry point
└── requirements.txt
```

## Output Specs

| Wrap Type | Dimensions (in) | Pixels @ 300 DPI | Format |
|-----------|-----------------|-------------------|--------|
| Straight  | 9.3 × 8.2       | 2790 × 2460       | PNG    |
| Tapered   | 9.45 × 8.25     | 2835 × 2475       | PNG    |

- **Resampling:** Lanczos (highest quality)
- **Strategy:** Cover-resize → center-crop (no white bars)
- **DPI metadata** embedded in output files

## Configuration

Edit `config.py` to change dimensions, DPI, minimum resolution, naming, etc.

## Future Phases (Roadmap)

- [ ] AI upscaling (Real-ESRGAN / ESPCN via GPU)
- [ ] Google Drive auto-upload
- [ ] PDF generation for print shops
- [ ] Listing mockup image generation
- [ ] SEO metadata / CSV generation
- [ ] File watcher (auto-detect new files)
