from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.session import Base, get_db
from app.main import app
from app.storage.local import LocalStorage


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    storage = LocalStorage(tmp_path / "uploads")

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr("app.services.images.get_storage", lambda settings=None: storage)

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _png_bytes(size=(64, 48), color=(20, 40, 80)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def test_health(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_upload_png_returns_preview_urls(client: TestClient):
    files = {"file": ("sample.png", _png_bytes(), "image/png")}
    res = client.post("/api/images/upload", files=files)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "uploaded"
    assert body["original_filename"].endswith(".png")
    assert body["original_url"].startswith("/uploads/")
    assert body["current_url"] == body["original_url"]
    assert body["id"]

    get_res = client.get(f"/api/images/{body['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == body["id"]

    status_res = client.get(f"/api/images/{body['id']}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "uploaded"


def test_reject_non_image(client: TestClient):
    files = {"file": ("notes.txt", b"hello", "text/plain")}
    res = client.post("/api/images/upload", files=files)
    assert res.status_code == 400


def test_reject_oversized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.images.get_settings", lambda: Settings(max_upload_bytes=100))
    files = {"file": ("big.png", _png_bytes(size=(400, 400)), "image/png")}
    res = client.post("/api/images/upload", files=files)
    assert res.status_code == 400
    assert "large" in res.json()["detail"].lower()


def test_prepare_returns_laser_ready_png(client: TestClient):
    files = {"file": ("sample.png", _png_bytes(size=(120, 80), color=(210, 40, 40)), "image/png")}
    uploaded = client.post("/api/images/upload", files=files)
    assert uploaded.status_code == 200, uploaded.text
    job_id = uploaded.json()["id"]

    prepared = client.post(
        f"/api/images/{job_id}/prepare",
        json={
            "mode": "floyd",
            "contrast": 1.6,
            "brightness": 1.05,
            "sharpness": 1.2,
            "denoise": 0.3,
            "invert": False,
            "width_mm": 50,
            "dpi": 300,
        },
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["status"] == "ready"
    assert body["prepared_url"]
    assert body["prepared_url"].endswith(".png")
    assert body["dpi"] == 300
    assert body["width_mm"] is not None
    assert body["height_mm"] is not None
    # 50mm @ 300 DPI ≈ 591 px wide
    assert body["width"] == 591

    recent = client.get("/api/images/?limit=5")
    assert recent.status_code == 200
    ids = [item["id"] for item in recent.json()]
    assert job_id in ids


def test_prepare_threshold_mode(client: TestClient):
    files = {"file": ("line.png", _png_bytes(size=(80, 60), color=(30, 30, 30)), "image/png")}
    uploaded = client.post("/api/images/upload", files=files)
    job_id = uploaded.json()["id"]
    prepared = client.post(
        f"/api/images/{job_id}/prepare",
        json={"mode": "threshold", "threshold": 100, "invert": True},
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["status"] == "ready"


def test_edit_requires_api_key(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "app.services.images.get_settings",
        lambda: Settings(gemini_api_key="", openai_api_key="", image_edit_provider="auto"),
    )
    files = {"file": ("sample.png", _png_bytes(), "image/png")}
    uploaded = client.post("/api/images/upload", files=files)
    job_id = uploaded.json()["id"]
    res = client.post(f"/api/images/{job_id}/edit", json={"prompt": "remove the background"})
    assert res.status_code == 400
    assert "GEMINI_API_KEY" in res.json()["detail"] or "API_KEY" in res.json()["detail"]


def test_revert_ai_edits(client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    from app.services import images as image_service

    def fake_edit(_settings, image_bytes: bytes, prompt: str) -> bytes:
        # Return a distinct tiny PNG so storage keys differ
        color = (10, 200, 40) if "second" in prompt else (200, 20, 20)
        return _png_bytes(size=(32, 24), color=color)

    monkeypatch.setattr(image_service, "edit_image", fake_edit)
    files = {"file": ("sample.png", _png_bytes(), "image/png")}
    uploaded = client.post("/api/images/upload", files=files)
    job_id = uploaded.json()["id"]

    first = client.post(f"/api/images/{job_id}/edit", json={"prompt": "first edit please"})
    assert first.status_code == 200, first.text
    assert first.json()["edit_count"] == 1
    assert first.json()["can_undo_edit"] is True
    first_edited = first.json()["edited_url"]

    second = client.post(f"/api/images/{job_id}/edit", json={"prompt": "second edit please"})
    assert second.status_code == 200, second.text
    assert second.json()["edit_count"] == 2
    assert second.json()["edited_url"] != first_edited

    undo = client.post(f"/api/images/{job_id}/revert", json={"target": "previous"})
    assert undo.status_code == 200, undo.text
    assert undo.json()["edit_count"] == 1
    assert undo.json()["edited_url"] == first_edited

    original = client.post(f"/api/images/{job_id}/revert", json={"target": "original"})
    assert original.status_code == 200, original.text
    assert original.json()["edit_count"] == 0
    assert original.json()["can_undo_edit"] is False
    assert original.json()["edited_url"] is None
    assert original.json()["status"] == "uploaded"


def test_delete_job(client: TestClient):
    files = {"file": ("gone.png", _png_bytes(), "image/png")}
    uploaded = client.post("/api/images/upload", files=files)
    job_id = uploaded.json()["id"]
    deleted = client.delete(f"/api/images/{job_id}")
    assert deleted.status_code == 204, deleted.text
    missing = client.get(f"/api/images/{job_id}")
    assert missing.status_code == 404
    recent = client.get("/api/images/?limit=10")
    assert job_id not in [item["id"] for item in recent.json()]
