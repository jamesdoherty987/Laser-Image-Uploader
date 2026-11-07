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
