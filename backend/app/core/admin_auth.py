"""Lightweight admin bearer tokens (HMAC) — no extra auth package needed."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings

bearer = HTTPBearer(auto_error=False)
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7


def _b64(data: bytes) -> str:
    return urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return urlsafe_b64decode(data + padding)


def create_admin_token(settings: Settings | None = None) -> str:
    cfg = settings or get_settings()
    payload = {"role": "admin", "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(cfg.secret_key.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_admin_token(token: str, settings: Settings | None = None) -> bool:
    cfg = settings or get_settings()
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        return False
    expected = hmac.new(cfg.secret_key.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return False
    try:
        payload = json.loads(_unb64(body))
    except (json.JSONDecodeError, ValueError):
        return False
    if payload.get("role") != "admin":
        return False
    exp = int(payload.get("exp") or 0)
    return exp >= int(time.time())


def password_matches(password: str, settings: Settings | None = None) -> bool:
    cfg = settings or get_settings()
    return secrets.compare_digest(password, cfg.admin_password)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_settings),
) -> None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin login required.")
    if not verify_admin_token(credentials.credentials, settings):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired admin token.")
