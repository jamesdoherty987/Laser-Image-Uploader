"""Download prepared laser PNGs to a local folder."""

from __future__ import annotations

import urllib.request
from pathlib import Path


def download_file(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as res, dest.open("wb") as out:
        out.write(res.read())
    return dest


def absolute_media_url(api_base: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{api_base.rstrip('/')}{path if path.startswith('/') else '/' + path}"
