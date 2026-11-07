from pathlib import Path

import pytest
from fastapi.testclient import TestClient
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
    settings = Settings(secret_key="test-secret", admin_username="admin", admin_password="test-pass")

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


def test_public_contact_defaults_and_admin_update(client):
    test_client, settings = client
    public = test_client.get("/api/content/contact")
    assert public.status_code == 200
    body = public.json()
    assert body["business_name"] == "Galvin Crafts"
    assert body["email"]

    headers = {"Authorization": f"Bearer {create_admin_token(settings)}"}
    updated = test_client.put(
        "/api/admin/contact",
        headers=headers,
        json={
            "email": "orders@galvincrafts.ie",
            "phone": "+353 86 123 4567",
            "location": "Cork, Ireland",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["email"] == "orders@galvincrafts.ie"
    assert updated.json()["phone"] == "+353 86 123 4567"

    again = test_client.get("/api/content/contact")
    assert again.json()["email"] == "orders@galvincrafts.ie"
    assert again.json()["location"] == "Cork, Ireland"
