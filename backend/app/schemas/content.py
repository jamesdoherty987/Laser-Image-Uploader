from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LandingImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    alt_text: str
    section: str
    image_url: str
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LandingImageUpdate(BaseModel):
    title: str | None = None
    alt_text: str | None = None
    section: str | None = Field(default=None, pattern="^(hero|gallery)$")
    sort_order: int | None = None
    is_active: bool | None = None


class CraftTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    category: str
    image_url: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CraftTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = ""
    category: str = "General"
    sort_order: int = 0
    is_active: bool = True


class CraftTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    category: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    category: str
    price_cents: int
    currency: str
    image_url: str | None
    sort_order: int
    is_active: bool
    stripe_price_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = ""
    category: str = "General"
    price_cents: int = Field(default=0, ge=0, le=10_000_000)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    sort_order: int = 0
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    category: str | None = None
    price_cents: int | None = Field(default=None, ge=0, le=10_000_000)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    sort_order: int | None = None
    is_active: bool | None = None
    stripe_price_id: str | None = None


class SiteContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_name: str
    tagline: str
    email: str
    phone: str
    location: str
    hours: str
    instagram: str
    website: str
    message: str
    updated_at: datetime


class SiteContactUpdate(BaseModel):
    business_name: str | None = Field(default=None, max_length=160)
    tagline: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=255)
    hours: str | None = Field(default=None, max_length=255)
    instagram: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=255)
    message: str | None = None


class AdminLoginIn(BaseModel):
    username: str
    password: str


class AdminLoginOut(BaseModel):
    token: str
    username: str
