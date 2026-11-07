"""Build a downloadable zip of the desktop connector for admin."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

# backend/app/services -> parents[3] = repo root
REPO_ROOT = Path(__file__).resolve().parents[3]
DESKTOP_DIR = REPO_ROOT / "desktop"

INCLUDE_NAMES = {
    "README.md",
    "run_connector.bat",
    "coreldraw_connector/main.py",
    "coreldraw_connector/api_client.py",
    "coreldraw_connector/config.py",
    "coreldraw_connector/downloader.py",
    "coreldraw_connector/coreldraw.py",
}


def build_desktop_zip() -> bytes:
    if not DESKTOP_DIR.is_dir():
        raise FileNotFoundError("Desktop connector folder is missing.")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in sorted(INCLUDE_NAMES):
            path = DESKTOP_DIR / rel
            if not path.is_file():
                continue
            zf.write(path, arcname=f"galvin-crafts-desktop/{rel}")
        # Ensure empty package marker if somehow empty
        if zf.namelist() == []:
            zf.writestr("galvin-crafts-desktop/README.md", "Desktop connector unavailable.\n")
    return buf.getvalue()
