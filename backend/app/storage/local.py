"""Local filesystem storage with a key-based API ready for cloud object storage."""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        for sub in ("originals", "edited", "prepared", "tmp"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        # Prevent path traversal — keys must stay under storage root
        cleaned = key.replace("\\", "/").lstrip("/")
        if ".." in cleaned.split("/"):
            raise ValueError("Invalid storage key")
        path = (self.root / cleaned).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key")
        return path

    def save_bytes(self, key: str, data: bytes) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        logger.info("Saved %s (%s bytes)", key, len(data))
        return key

    def read_bytes(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._resolve(key).is_file()

    def absolute_path(self, key: str) -> Path:
        return self._resolve(key)

    def public_url_path(self, key: str) -> str:
        """URL path served by FastAPI StaticFiles mount."""
        return f"/uploads/{key.lstrip('/')}"

    @staticmethod
    def make_key(folder: str, filename: str, job_id: str | None = None) -> str:
        stem = Path(filename).stem
        suffix = Path(filename).suffix.lower() or ".bin"
        safe = SAFE_NAME.sub("_", stem).strip("._") or "image"
        uid = job_id or str(uuid.uuid4())
        return f"{folder}/{uid}/{safe}{suffix}"


def get_storage(settings: Settings | None = None) -> LocalStorage:
    cfg = settings or get_settings()
    return LocalStorage(cfg.storage_path())
