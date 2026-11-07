"""Auth for the Windows desktop connector via pairing token."""

from __future__ import annotations

import logging
import secrets
from pathlib import Path

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_TOKEN_FILE = Path(__file__).resolve().parents[2] / ".desktop_pairing_token"
_cached_token: str | None = None


def _read_token_file() -> str:
    try:
        if _TOKEN_FILE.is_file():
            return _TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        logger.warning("Could not read desktop pairing token file.")
    return ""


def _write_token_file(token: str) -> None:
    try:
        _TOKEN_FILE.write_text(token, encoding="utf-8")
    except OSError:
        logger.warning("Could not persist desktop pairing token file.")


def ensure_pairing_token(settings: Settings | None = None) -> str:
    """Return a stable pairing token (settings env → local file → generate)."""
    global _cached_token
    cfg = settings or get_settings()
    env_token = (cfg.desktop_pairing_token or "").strip()
    if env_token:
        _cached_token = env_token
        return env_token

    if _cached_token:
        return _cached_token

    token = _read_token_file()
    if not token:
        token = secrets.token_urlsafe(24)
        _write_token_file(token)
        logger.info("Generated desktop pairing token and saved to %s", _TOKEN_FILE.name)

    _cached_token = token
    return token


def require_desktop(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = ensure_pairing_token(settings)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Desktop pairing token required.",
        )
    provided = authorization.split(" ", 1)[1].strip()
    if not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid desktop pairing token.",
        )
