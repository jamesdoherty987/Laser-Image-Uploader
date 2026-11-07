from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: JobStatus
    original_filename: str
    content_type: str
    original_url: str
    current_url: str
    edited_url: str | None = None
    prepared_url: str | None = None
    error_message: str | None = None
    width: int | None = None
    height: int | None = None
    dpi: int | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    created_at: datetime
    updated_at: datetime


class JobStatusOut(BaseModel):
    id: str
    status: JobStatus
    error_message: str | None = None


class PrepareOptions(BaseModel):
    mode: Literal[
        "floyd",
        "jarvis",
        "stucki",
        "atkinson",
        "ordered",
        "threshold",
        "grayscale",
        "dither",
    ] = "floyd"
    contrast: float = Field(default=1.55, ge=0.5, le=2.5)
    brightness: float = Field(default=1.05, ge=0.4, le=2.0)
    sharpness: float = Field(default=1.1, ge=0.0, le=3.0)
    denoise: float = Field(default=0.35, ge=0.0, le=1.0)
    invert: bool = False
    threshold: int = Field(default=128, ge=1, le=254)
    width_mm: float | None = Field(default=None, ge=5, le=600)
    height_mm: float | None = Field(default=None, ge=5, le=600)
    dpi: int = Field(default=300, ge=72, le=600)


class EditPrompt(BaseModel):
    prompt: str = Field(min_length=3, max_length=800)


class JobStatusUpdate(BaseModel):
    status: JobStatus
    error_message: str | None = None


class DesktopFailIn(BaseModel):
    error_message: str = Field(default="Desktop connector failed.", max_length=500)


class DesktopInfoOut(BaseModel):
    pairing_token: str
    api_base: str
    download_path: str = "/api/admin/desktop/download"
    instructions: str
