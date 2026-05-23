"""
Google Drive Uploader
─────────────────────
Uploads straight_wraps/ and tapered_wraps/ for a bundle to Google Drive.

Flow:
  Drive parent folder (DRIVE_PARENT_FOLDER_ID)
  └── <bundle_name>/
      ├── straight_wraps/   ← all PNG files uploaded here
      └── tapered_wraps/    ← all PNG files uploaded here

Returns the shareable link to the bundle folder and logs to drive_ledger.csv.

First run: opens a browser window for one-time Google OAuth consent.
Subsequent runs: uses the saved token in credentials/google_token.json.

Setup (one-time):
  1. Go to https://console.cloud.google.com/
  2. New project → Enable Google Drive API
  3. Credentials → Create OAuth 2.0 Client ID (Desktop app)
  4. Download JSON → save as  credentials/google_credentials.json
  5. Set DRIVE_PARENT_FOLDER_ID in config.py (the ID of your Drive folder)
  6. Set DRIVE_UPLOAD_ENABLED = True in config.py
"""

import csv
import logging
import mimetypes
from datetime import datetime
from pathlib import Path

from config import (
    DRIVE_UPLOAD_ENABLED,
    DRIVE_CREDENTIALS_FILE,
    DRIVE_TOKEN_FILE,
    DRIVE_PARENT_FOLDER_ID,
    OUTPUT_DIR,
)

logger = logging.getLogger("etsy_tumbler")

LEDGER_FILE = Path(__file__).parent / "drive_ledger.csv"
LEDGER_HEADERS = ["bundle_name", "upload_date", "drive_folder_id", "shareable_link"]

SCOPES = ["https://www.googleapis.com/auth/drive"]


# ──────────────────────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────────────────────

def _get_drive_service():
    """Authenticate and return a Drive API service object."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if DRIVE_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(DRIVE_TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(DRIVE_CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        DRIVE_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        DRIVE_TOKEN_FILE.write_text(creds.to_json())

    return build("drive", "v3", credentials=creds)


# ──────────────────────────────────────────────────────────────
# Drive helpers
# ──────────────────────────────────────────────────────────────

def _create_folder(service, name: str, parent_id: str) -> str:
    """Create a Drive folder and return its ID."""
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def _upload_file(service, local_path: Path, parent_id: str) -> str:
    """Upload a file to Drive and return its ID."""
    from googleapiclient.http import MediaFileUpload

    mime, _ = mimetypes.guess_type(str(local_path))
    mime = mime or "application/octet-stream"

    meta = {"name": local_path.name, "parents": [parent_id]}
    media = MediaFileUpload(str(local_path), mimetype=mime, resumable=True)
    f = service.files().create(body=meta, media_body=media, fields="id").execute()
    return f["id"]


def _make_public(service, file_id: str) -> str:
    """Grant 'anyone with the link can view' and return the web link."""
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()
    file = service.files().get(fileId=file_id, fields="webViewLink").execute()
    return file["webViewLink"]


# ──────────────────────────────────────────────────────────────
# Ledger
# ──────────────────────────────────────────────────────────────

def _append_ledger(bundle_name: str, folder_id: str, link: str):
    """Append one row to drive_ledger.csv."""
    write_header = not LEDGER_FILE.exists()
    with open(LEDGER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_HEADERS)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "bundle_name":    bundle_name,
            "upload_date":    datetime.now().strftime("%Y-%m-%d %H:%M"),
            "drive_folder_id": folder_id,
            "shareable_link": link,
        })


# ──────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────

def upload_bundle_to_drive(bundle_name: str) -> str | None:
    """
    Upload straight_wraps/ and tapered_wraps/ for *bundle_name* to Drive.

    Returns the shareable link to the bundle Drive folder, or None on failure.
    """
    if not DRIVE_UPLOAD_ENABLED:
        logger.info("  [DRIVE] Upload disabled (DRIVE_UPLOAD_ENABLED=False in config.py)")
        return None

    if not DRIVE_PARENT_FOLDER_ID:
        logger.error("  [DRIVE] DRIVE_PARENT_FOLDER_ID is empty — set it in config.py")
        return None

    if not DRIVE_CREDENTIALS_FILE.exists():
        logger.error(
            "  [DRIVE] Credentials not found at %s\n"
            "  Download from Google Cloud Console → APIs & Services → Credentials",
            DRIVE_CREDENTIALS_FILE,
        )
        return None

    bundle_out = OUTPUT_DIR / bundle_name
    straight_dir = bundle_out / "straight_wraps"
    tapered_dir  = bundle_out / "tapered_wraps"

    if not straight_dir.exists() and not tapered_dir.exists():
        logger.error("  [DRIVE] No wrap folders found in %s", bundle_out)
        return None

    logger.info("  [DRIVE] Authenticating with Google Drive…")
    try:
        service = _get_drive_service()
    except Exception as e:
        logger.error("  [DRIVE] Auth failed: %s", e)
        return None

    # Create top-level bundle folder in Drive
    logger.info("  [DRIVE] Creating Drive folder: %s", bundle_name)
    bundle_folder_id = _create_folder(service, bundle_name, DRIVE_PARENT_FOLDER_ID)

    # Upload each wrap subfolder
    for local_dir, subfolder_name in [
        (straight_dir, "straight_wraps"),
        (tapered_dir,  "tapered_wraps"),
    ]:
        if not local_dir.exists():
            logger.warning("  [DRIVE] %s not found — skipping", local_dir)
            continue

        files = sorted(local_dir.iterdir())
        if not files:
            logger.warning("  [DRIVE] %s is empty — skipping", local_dir)
            continue

        sub_id = _create_folder(service, subfolder_name, bundle_folder_id)
        logger.info("  [DRIVE] Uploading %d files → %s/", len(files), subfolder_name)

        for i, fp in enumerate(files, 1):
            if fp.is_file():
                _upload_file(service, fp, sub_id)
                logger.info("    [%d/%d] %s", i, len(files), fp.name)

    # Make bundle folder public and get link
    link = _make_public(service, bundle_folder_id)
    logger.info("  [DRIVE] Shareable link: %s", link)

    # Record in ledger
    _append_ledger(bundle_name, bundle_folder_id, link)
    logger.info("  [DRIVE] Ledger updated → drive_ledger.csv")

    return link
