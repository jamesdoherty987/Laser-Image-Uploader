from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.admin_auth import create_admin_token, password_matches, require_admin
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.content import (
    AdminLoginIn,
    AdminLoginOut,
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
from app.services import content as content_service

router = APIRouter(tags=["content"])
admin_router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/admin/login", response_model=AdminLoginOut)
def admin_login(payload: AdminLoginIn, settings: Settings = Depends(get_settings)) -> AdminLoginOut:
    if payload.username != settings.admin_username or not password_matches(payload.password, settings):
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Invalid admin credentials.")
    return AdminLoginOut(token=create_admin_token(settings), username=settings.admin_username)


@router.get("/content/landing-images", response_model=list[LandingImageOut])
def public_landing_images(
    section: str | None = None,
    db: Session = Depends(get_db),
) -> list[LandingImageOut]:
    return content_service.list_landing_images(db, active_only=True, section=section)


@router.get("/content/templates", response_model=list[CraftTemplateOut])
def public_templates(db: Session = Depends(get_db)) -> list[CraftTemplateOut]:
    return content_service.list_templates(db, active_only=True)


@router.get("/content/products", response_model=list[ProductOut])
def public_products(db: Session = Depends(get_db)) -> list[ProductOut]:
    return content_service.list_products(db, active_only=True)


@router.get("/content/contact", response_model=SiteContactOut)
def public_contact(db: Session = Depends(get_db)) -> SiteContactOut:
    return content_service.get_contact(db)


@admin_router.get("/landing-images", response_model=list[LandingImageOut])
def admin_list_landing_images(db: Session = Depends(get_db)) -> list[LandingImageOut]:
    return content_service.list_landing_images(db, active_only=False)


@admin_router.post("/landing-images", response_model=LandingImageOut)
async def admin_create_landing_image(
    file: UploadFile = File(...),
    title: str = Form(""),
    alt_text: str = Form(""),
    section: str = Form("hero"),
    db: Session = Depends(get_db),
) -> LandingImageOut:
    return content_service.create_landing_image(
        db,
        file,
        title=title,
        alt_text=alt_text,
        section=section,
    )


@admin_router.patch("/landing-images/{image_id}", response_model=LandingImageOut)
def admin_update_landing_image(
    image_id: str,
    payload: LandingImageUpdate,
    db: Session = Depends(get_db),
) -> LandingImageOut:
    return content_service.update_landing_image(db, image_id, payload)


@admin_router.delete("/landing-images/{image_id}")
def admin_delete_landing_image(image_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    content_service.delete_landing_image(db, image_id)
    return {"status": "deleted"}


@admin_router.get("/templates", response_model=list[CraftTemplateOut])
def admin_list_templates(db: Session = Depends(get_db)) -> list[CraftTemplateOut]:
    return content_service.list_templates(db, active_only=False)


@admin_router.post("/templates", response_model=CraftTemplateOut)
async def admin_create_template(
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("General"),
    sort_order: int = Form(0),
    is_active: bool = Form(True),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> CraftTemplateOut:
    payload = CraftTemplateCreate(
        name=name,
        description=description,
        category=category,
        sort_order=sort_order,
        is_active=is_active,
    )
    return content_service.create_template(db, payload, upload=file)


@admin_router.patch("/templates/{template_id}", response_model=CraftTemplateOut)
async def admin_update_template(
    template_id: str,
    name: str | None = Form(None),
    description: str | None = Form(None),
    category: str | None = Form(None),
    sort_order: int | None = Form(None),
    is_active: bool | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> CraftTemplateOut:
    payload = CraftTemplateUpdate(
        name=name,
        description=description,
        category=category,
        sort_order=sort_order,
        is_active=is_active,
    )
    return content_service.update_template(db, template_id, payload, upload=file)


@admin_router.delete("/templates/{template_id}")
def admin_delete_template(template_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    content_service.delete_template(db, template_id)
    return {"status": "deleted"}


@admin_router.get("/products", response_model=list[ProductOut])
def admin_list_products(db: Session = Depends(get_db)) -> list[ProductOut]:
    return content_service.list_products(db, active_only=False)


@admin_router.post("/products", response_model=ProductOut)
async def admin_create_product(
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("General"),
    price_cents: int = Form(0),
    currency: str = Form("EUR"),
    sort_order: int = Form(0),
    is_active: bool = Form(True),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> ProductOut:
    payload = ProductCreate(
        name=name,
        description=description,
        category=category,
        price_cents=price_cents,
        currency=currency,
        sort_order=sort_order,
        is_active=is_active,
    )
    return content_service.create_product(db, payload, upload=file)


@admin_router.patch("/products/{product_id}", response_model=ProductOut)
async def admin_update_product(
    product_id: str,
    name: str | None = Form(None),
    description: str | None = Form(None),
    category: str | None = Form(None),
    price_cents: int | None = Form(None),
    currency: str | None = Form(None),
    sort_order: int | None = Form(None),
    is_active: bool | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> ProductOut:
    payload = ProductUpdate(
        name=name,
        description=description,
        category=category,
        price_cents=price_cents,
        currency=currency,
        sort_order=sort_order,
        is_active=is_active,
    )
    return content_service.update_product(db, product_id, payload, upload=file)


@admin_router.delete("/products/{product_id}")
def admin_delete_product(product_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    content_service.delete_product(db, product_id)
    return {"status": "deleted"}


@admin_router.get("/contact", response_model=SiteContactOut)
def admin_get_contact(db: Session = Depends(get_db)) -> SiteContactOut:
    return content_service.get_contact(db)


@admin_router.put("/contact", response_model=SiteContactOut)
def admin_update_contact(
    payload: SiteContactUpdate,
    db: Session = Depends(get_db),
) -> SiteContactOut:
    return content_service.update_contact(db, payload)
