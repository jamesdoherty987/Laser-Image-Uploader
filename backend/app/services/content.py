"""Landing images, craft templates, and shop products."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.content import CraftTemplate, LandingImage, Product, SiteContact
from app.schemas.content import (
    CraftTemplateCreate,
    CraftTemplateOut,
    CraftTemplateUpdate,
    LandingImageOut,
    LandingImageUpdate,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    SiteContactOut,
    SiteContactUpdate,
)
from app.storage.local import LocalStorage, get_storage

DEFAULT_CONTACT = {
    "id": "default",
    "business_name": "Galvin Crafts",
    "tagline": "Custom laser engraving",
    "email": "hello@galvincrafts.ie",
    "phone": "+353 87 000 0000",
    "location": "Ireland",
    "hours": "Mon–Sat, by appointment",
    "instagram": "@galvincrafts",
    "website": "",
    "message": "Questions about an order or a custom piece? Send a message — happy to help.",
}

logger = logging.getLogger(__name__)

ALLOWED = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _read_image(upload: UploadFile, settings: Settings) -> tuple[bytes, str, str]:
    filename = upload.filename or "image.png"
    content_type = (upload.content_type or "").lower().strip()
    if content_type not in ALLOWED:
        raise HTTPException(status_code=400, detail="Upload JPG, PNG or WEBP.")
    data = upload.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="File too large.")
    try:
        with Image.open(BytesIO(data)) as img:
            img.verify()
        with Image.open(BytesIO(data)) as img:
            fmt = (img.format or "").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail="Could not read image.") from exc
    expected = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    if fmt not in expected:
        raise HTTPException(status_code=400, detail="Unsupported image format.")
    content_type = expected[fmt]
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED[content_type]:
        suffix = next(iter(ALLOWED[content_type]))
    safe = f"{Path(filename).stem or 'image'}{suffix}"
    return data, safe, content_type


def landing_to_out(row: LandingImage, storage: LocalStorage) -> LandingImageOut:
    return LandingImageOut(
        id=row.id,
        title=row.title,
        alt_text=row.alt_text,
        section=row.section,
        image_url=storage.public_url_path(row.image_key),
        sort_order=row.sort_order,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def template_to_out(row: CraftTemplate, storage: LocalStorage) -> CraftTemplateOut:
    return CraftTemplateOut(
        id=row.id,
        name=row.name,
        description=row.description,
        category=row.category,
        image_url=storage.public_url_path(row.image_key) if row.image_key else None,
        sort_order=row.sort_order,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def list_landing_images(
    db: Session,
    *,
    active_only: bool = True,
    section: str | None = None,
    storage: LocalStorage | None = None,
) -> list[LandingImageOut]:
    store = storage or get_storage()
    q = db.query(LandingImage)
    if active_only:
        q = q.filter(LandingImage.is_active.is_(True))
    if section:
        q = q.filter(LandingImage.section == section)
    rows = q.order_by(LandingImage.sort_order.asc(), LandingImage.created_at.desc()).all()
    return [landing_to_out(row, store) for row in rows]


def create_landing_image(
    db: Session,
    upload: UploadFile,
    *,
    title: str = "",
    alt_text: str = "",
    section: str = "hero",
    storage: LocalStorage | None = None,
    settings: Settings | None = None,
) -> LandingImageOut:
    cfg = settings or get_settings()
    store = storage or get_storage(cfg)
    if section not in {"hero", "gallery"}:
        raise HTTPException(status_code=400, detail="Section must be hero or gallery.")
    data, filename, _ = _read_image(upload, cfg)
    row = LandingImage(title=title.strip(), alt_text=alt_text.strip() or title.strip(), section=section)
    db.add(row)
    db.flush()
    key = store.make_key("landing", filename, row.id)
    store.save_bytes(key, data)
    row.image_key = key
    row.sort_order = int(db.query(LandingImage).count())
    db.commit()
    db.refresh(row)
    return landing_to_out(row, store)


def update_landing_image(
    db: Session,
    image_id: str,
    payload: LandingImageUpdate,
    storage: LocalStorage | None = None,
) -> LandingImageOut:
    store = storage or get_storage()
    row = db.get(LandingImage, image_id)
    if not row:
        raise HTTPException(status_code=404, detail="Landing image not found.")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return landing_to_out(row, store)


def delete_landing_image(db: Session, image_id: str) -> None:
    row = db.get(LandingImage, image_id)
    if not row:
        raise HTTPException(status_code=404, detail="Landing image not found.")
    db.delete(row)
    db.commit()


def list_templates(
    db: Session,
    *,
    active_only: bool = True,
    storage: LocalStorage | None = None,
) -> list[CraftTemplateOut]:
    store = storage or get_storage()
    q = db.query(CraftTemplate)
    if active_only:
        q = q.filter(CraftTemplate.is_active.is_(True))
    rows = q.order_by(CraftTemplate.sort_order.asc(), CraftTemplate.created_at.desc()).all()
    return [template_to_out(row, store) for row in rows]


def create_template(
    db: Session,
    payload: CraftTemplateCreate,
    upload: UploadFile | None = None,
    storage: LocalStorage | None = None,
    settings: Settings | None = None,
) -> CraftTemplateOut:
    cfg = settings or get_settings()
    store = storage or get_storage(cfg)
    row = CraftTemplate(
        name=payload.name.strip(),
        description=payload.description.strip(),
        category=payload.category.strip() or "General",
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    db.add(row)
    db.flush()
    if upload is not None and upload.filename:
        data, filename, _ = _read_image(upload, cfg)
        key = store.make_key("templates", filename, row.id)
        store.save_bytes(key, data)
        row.image_key = key
    db.commit()
    db.refresh(row)
    return template_to_out(row, store)


def update_template(
    db: Session,
    template_id: str,
    payload: CraftTemplateUpdate,
    upload: UploadFile | None = None,
    storage: LocalStorage | None = None,
    settings: Settings | None = None,
) -> CraftTemplateOut:
    cfg = settings or get_settings()
    store = storage or get_storage(cfg)
    row = db.get(CraftTemplate, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="Template not found.")
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in data.items():
        setattr(row, key, value)
    if upload is not None and upload.filename:
        file_data, filename, _ = _read_image(upload, cfg)
        key = store.make_key("templates", filename, row.id)
        store.save_bytes(key, file_data)
        row.image_key = key
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return template_to_out(row, store)


def delete_template(db: Session, template_id: str) -> None:
    row = db.get(CraftTemplate, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="Template not found.")
    db.delete(row)
    db.commit()


def product_to_out(row: Product, storage: LocalStorage) -> ProductOut:
    return ProductOut(
        id=row.id,
        name=row.name,
        description=row.description,
        category=row.category,
        price_cents=row.price_cents,
        currency=row.currency,
        image_url=storage.public_url_path(row.image_key) if row.image_key else None,
        sort_order=row.sort_order,
        is_active=row.is_active,
        stripe_price_id=row.stripe_price_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def list_products(
    db: Session,
    *,
    active_only: bool = True,
    storage: LocalStorage | None = None,
) -> list[ProductOut]:
    store = storage or get_storage()
    q = db.query(Product)
    if active_only:
        q = q.filter(Product.is_active.is_(True))
    rows = q.order_by(Product.sort_order.asc(), Product.created_at.desc()).all()
    return [product_to_out(row, store) for row in rows]


def create_product(
    db: Session,
    payload: ProductCreate,
    upload: UploadFile | None = None,
    storage: LocalStorage | None = None,
    settings: Settings | None = None,
) -> ProductOut:
    cfg = settings or get_settings()
    store = storage or get_storage(cfg)
    row = Product(
        name=payload.name.strip(),
        description=payload.description.strip(),
        category=payload.category.strip() or "General",
        price_cents=payload.price_cents,
        currency=(payload.currency or "EUR").strip().upper(),
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    db.add(row)
    db.flush()
    if upload is not None and upload.filename:
        data, filename, _ = _read_image(upload, cfg)
        key = store.make_key("products", filename, row.id)
        store.save_bytes(key, data)
        row.image_key = key
    db.commit()
    db.refresh(row)
    return product_to_out(row, store)


def update_product(
    db: Session,
    product_id: str,
    payload: ProductUpdate,
    upload: UploadFile | None = None,
    storage: LocalStorage | None = None,
    settings: Settings | None = None,
) -> ProductOut:
    cfg = settings or get_settings()
    store = storage or get_storage(cfg)
    row = db.get(Product, product_id)
    if not row:
        raise HTTPException(status_code=404, detail="Product not found.")
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "currency" in data and isinstance(data["currency"], str):
        data["currency"] = data["currency"].strip().upper()
    if "name" in data and isinstance(data["name"], str):
        data["name"] = data["name"].strip()
    if "category" in data and isinstance(data["category"], str):
        data["category"] = data["category"].strip() or "General"
    if "description" in data and isinstance(data["description"], str):
        data["description"] = data["description"].strip()
    for key, value in data.items():
        setattr(row, key, value)
    if upload is not None and upload.filename:
        file_data, filename, _ = _read_image(upload, cfg)
        key = store.make_key("products", filename, row.id)
        store.save_bytes(key, file_data)
        row.image_key = key
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return product_to_out(row, store)


def delete_product(db: Session, product_id: str) -> None:
    row = db.get(Product, product_id)
    if not row:
        raise HTTPException(status_code=404, detail="Product not found.")
    db.delete(row)
    db.commit()


def contact_to_out(row: SiteContact) -> SiteContactOut:
    return SiteContactOut(
        business_name=row.business_name,
        tagline=row.tagline,
        email=row.email,
        phone=row.phone,
        location=row.location,
        hours=row.hours,
        instagram=row.instagram,
        website=row.website,
        message=row.message,
        updated_at=row.updated_at,
    )


def ensure_contact(db: Session) -> SiteContact:
    row = db.get(SiteContact, "default")
    if row:
        return row
    row = SiteContact(**DEFAULT_CONTACT)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_contact(db: Session) -> SiteContactOut:
    return contact_to_out(ensure_contact(db))


def update_contact(db: Session, payload: SiteContactUpdate) -> SiteContactOut:
    row = ensure_contact(db)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(row, key, value)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return contact_to_out(row)
