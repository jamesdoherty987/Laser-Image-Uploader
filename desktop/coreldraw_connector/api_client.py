"""HTTP client for ready-job polling and status updates."""

from __future__ import annotations

from typing import Any

import urllib.error
import urllib.request
import json


class DesktopApiError(RuntimeError):
    pass


class DesktopApi:
    def __init__(self, api_base: str, pairing_token: str) -> None:
        self.api_base = api_base.rstrip("/")
        self.pairing_token = pairing_token.strip()

    def _request(self, method: str, path: str, body: dict | None = None) -> Any:
        url = f"{self.api_base}{path}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.pairing_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                raw = res.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise DesktopApiError(f"{exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise DesktopApiError(f"Cannot reach API at {self.api_base}: {exc.reason}") from exc

    def list_ready(self, limit: int = 20) -> list[dict]:
        return self._request("GET", f"/api/desktop/jobs?status=ready&limit={limit}")

    def claim(self, job_id: str) -> dict:
        return self._request("POST", f"/api/desktop/jobs/{job_id}/claim")

    def mark_imported(self, job_id: str) -> dict:
        return self._request("POST", f"/api/desktop/jobs/{job_id}/imported")

    def mark_failed(self, job_id: str, message: str) -> dict:
        return self._request(
            "POST",
            f"/api/desktop/jobs/{job_id}/failed",
            {"error_message": message},
        )
