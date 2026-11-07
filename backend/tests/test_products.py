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
    )

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr("app.services.content.get_storage", lambda settings=None: storage)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings

    with TestClient(app) as test_client:
        yield test_client, settings

    app.dependency_overrides.clear()


def _png_bytes() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (48, 48), (120, 80, 40)).save(buf, format="PNG")
    return buf.getvalue()


def _admin_headers(settings: Settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_admin_token(settings)}"}


def test_admin_can_create_and_list_products(client):
    test_client, settings = client
    headers = _admin_headers(settings)

    created = test_client.post(
        "/api/admin/products",
        headers=headers,
        data={
            "name": "Oak keyring",
            "description": "Laser-engraved oak",
            "category": "Keyrings",
            "price_cents": "1250",
            "currency": "EUR",
        },
        files={"file": ("oak.png", _png_bytes(), "image/png")},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["name"] == "Oak keyring"
    assert body["price_cents"] == 1250
    assert body["currency"] == "EUR"
    assert body["image_url"]
    product_id = body["id"]

    public = test_client.get("/api/content/products")
    assert public.status_code == 200
    assert any(item["id"] == product_id for item in public.json())

    updated = test_client.patch(
        f"/api/admin/products/{product_id}",
        headers=headers,
        data={"price_cents": "1999"},
    )
    assert updated.status_code == 200
    assert updated.json()["price_cents"] == 1999

    hidden = test_client.patch(
        f"/api/admin/products/{product_id}",
        headers=headers,
        data={"is_active": "false"},
    )
    assert hidden.status_code == 200
    public_after = test_client.get("/api/content/products")
    assert all(item["id"] != product_id for item in public_after.json())
