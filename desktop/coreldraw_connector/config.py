"""Local config for the Galvin Crafts desktop connector."""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".galvin-crafts" / "connector.json"
DEFAULT_DOWNLOAD_DIR = Path.home() / "GalvinCrafts" / "laser-ready"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {
            "api_base": "http://localhost:8000",
            "pairing_token": "",
            "poll_seconds": 8,
            "download_dir": str(DEFAULT_DOWNLOAD_DIR),
        }
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
