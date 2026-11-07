"""Example shop products backed by real laser-craft product photos."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.content import Product
from app.storage.local import LocalStorage, get_storage

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets" / "shop"

# Each entry maps to a real product photo under app/assets/shop/
EXAMPLE_PRODUCTS = [
    {
        "name": "Engraved oak plaque",
        "description": "Solid oak wall plaque with deep laser engraving — names, dates, or a short quote.",
        "category": "Home",
        "price_cents": 3500,
        "sort_order": 1,
        "image": "oak-name-plaque.jpg",
    },
    {
        "name": "Keepsake wood box",
        "description": "Hinged wooden box with a custom lid engraving — ideal for rings or letters.",
        "category": "Gifts",
        "price_cents": 4200,
        "sort_order": 2,
        "image": "keepsake-box.jpg",
    },
    {
        "name": "Round mountain coaster",
        "description": "Hardwood coaster with a mountain line engraving. Sold individually.",
        "category": "Home",
        "price_cents": 1200,
        "sort_order": 3,
        "image": "round-coaster.jpg",
    },
    {
        "name": "Maple key tag",
        "description": "Lightweight maple key tag with name or short message on both sides.",
        "category": "Everyday",
        "price_cents": 1000,
        "sort_order": 4,
        "image": "maple-key-tag.jpg",
    },
    {
        "name": "Serving board",
        "description": "Charcuterie-ready serving board with optional family name on the handle.",
        "category": "Kitchen",
        "price_cents": 4800,
        "sort_order": 5,
        "image": "serving-board.jpg",
    },
]


def _read_asset(filename: str) -> bytes:
    path = ASSETS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Missing shop asset: {path}")
    return path.read_bytes()


def _attach_image(store: LocalStorage, row: Product, filename: str) -> None:
    data = _read_asset(filename)
    key = store.make_key("products", filename, row.id)
    store.save_bytes(key, data)
    row.image_key = key


def seed_example_products(db: Session, storage: LocalStorage | None = None) -> int:
    """Insert / refresh example shop items with real product photos."""
    store = storage or get_storage()
    existing = {p.name: p for p in db.query(Product).all()}
    created = 0
    refreshed = 0
    keep = {item["name"] for item in EXAMPLE_PRODUCTS}

    for item in EXAMPLE_PRODUCTS:
        row = existing.get(item["name"])
        if row is None:
            row = Product(
                name=item["name"],
                description=item["description"],
                category=item["category"],
                price_cents=item["price_cents"],
                currency="EUR",
                sort_order=item["sort_order"],
                is_active=True,
            )
            db.add(row)
            db.flush()
            _attach_image(store, row, item["image"])
            created += 1
        else:
            row.description = item["description"]
            row.category = item["category"]
            row.sort_order = item["sort_order"]
            row.is_active = True
            _attach_image(store, row, item["image"])
            refreshed += 1

    # Drop previous placeholder / mismatched example SKUs
    for name, row in existing.items():
        if name not in keep:
            db.delete(row)

    db.commit()
    if created or refreshed:
        logger.info("Shop seed: created=%s refreshed_photos=%s", created, refreshed)
    return created + refreshed
