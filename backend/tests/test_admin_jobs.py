from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.admin_auth import create_admin_token
from app.core.config import Settings, get_settings
from app.core import desktop_auth
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
    settings = Settings(
        secret_key="test-secret",
        admin_username="admin",
        admin_password="test-pass",
        desktop_pairing_token="pair-token-abc",
        backend_url="http://testserver",
    )

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr("app.services.images.get_storage", lambda settings=None: storage)
    monkeypatch.setattr(desktop_auth, "_cached_token", None)
    monkeypatch.setattr(desktop_auth, "_TOKEN_FILE", tmp_path / ".desktop_pairing_token")
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings

    with TestClient(app) as test_client:
        yield test_client, settings

    app.dependency_overrides.clear()


def _png_bytes(size=(64, 48), color=(20, 40, 80)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _admin_headers(settings: Settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_admin_token(settings)}"}


def test_admin_sees_all_customer_jobs(client):
    test_client, settings = client
    uploaded = test_client.post(
        "/api/images/upload",
        files={"file": ("customer.png", _png_bytes(), "image/png")},
    )
    assert uploaded.status_code == 200
    job_id = uploaded.json()["id"]

    denied = test_client.get("/api/admin/jobs")
    assert denied.status_code == 401

    listed = test_client.get("/api/admin/jobs", headers=_admin_headers(settings))
    assert listed.status_code == 200
    ids = [item["id"] for item in listed.json()]
    assert job_id in ids


def test_admin_prepare_and_desktop_claim(client):
    test_client, settings = client
    headers = _admin_headers(settings)
    uploaded = test_client.post(
        "/api/images/upload",
        files={"file": ("cut-me.png", _png_bytes(size=(100, 80)), "image/png")},
    )
    job_id = uploaded.json()["id"]

    prepared = test_client.post(f"/api/admin/jobs/{job_id}/prepare", headers=headers, json={})
    assert prepared.status_code == 200
    assert prepared.json()["status"] == "ready"
    assert prepared.json()["prepared_url"]

    desktop_headers = {"Authorization": "Bearer pair-token-abc"}
    ready = test_client.get("/api/desktop/jobs?status=ready", headers=desktop_headers)
    assert ready.status_code == 200
    assert any(item["id"] == job_id for item in ready.json())

    claimed = test_client.post(f"/api/desktop/jobs/{job_id}/claim", headers=desktop_headers)
    assert claimed.status_code == 200
    assert claimed.json()["status"] == "downloading"

    imported = test_client.post(f"/api/desktop/jobs/{job_id}/imported", headers=desktop_headers)
    assert imported.status_code == 200
    assert imported.json()["status"] == "imported"


def test_admin_desktop_download_zip(client):
    test_client, settings = client
    headers = _admin_headers(settings)
    info = test_client.get("/api/admin/desktop", headers=headers)
    assert info.status_code == 200
    body = info.json()
    assert body["pairing_token"] == "pair-token-abc"
    assert body["download_path"] == "/api/admin/desktop/download"

    zip_res = test_client.get("/api/admin/desktop/download", headers=headers)
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"].startswith("application/zip")
    assert zip_res.content[:2] == b"PK"
