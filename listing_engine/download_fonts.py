"""Download Google Fonts for listing image generation."""
import urllib.request
import os

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")

FONT_URLS = {
    "Cinzel-Variable.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf",
    "CinzelDecorative-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzeldecorative/CinzelDecorative-Regular.ttf",
    "CinzelDecorative-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf",
    "Inter-Variable.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
}


def download_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    for filename, url in FONT_URLS.items():
        out_path = os.path.join(FONT_DIR, filename)
        if os.path.exists(out_path):
            print(f"  Already exists: {filename}")
            continue
        print(f"  Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, out_path)
            size = os.path.getsize(out_path)
            print(f"  OK: {size:,} bytes")
        except Exception as e:
            print(f"  FAILED: {e}")


if __name__ == "__main__":
    download_fonts()
