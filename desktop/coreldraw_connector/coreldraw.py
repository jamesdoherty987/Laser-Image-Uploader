"""Open prepared files in CorelDRAW when COM is available (Windows)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_in_coreldraw(path: Path) -> str:
    """Try CorelDRAW COM; fall back to the OS default image opener."""
    if sys.platform == "win32":
        try:
            import win32com.client  # type: ignore

            app = win32com.client.Dispatch("CorelDRAW.Application")
            app.Visible = True
            app.OpenDocument(str(path))
            return "coreldraw-com"
        except Exception:
            try:
                os.startfile(str(path))  # type: ignore[attr-defined]
                return "os-startfile"
            except OSError:
                pass

    # macOS / Linux fallback for local testing
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.run([opener, str(path)], check=False)
    return "fallback-open"
