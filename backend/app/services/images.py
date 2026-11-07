"""Image upload validation and job creation (Stage 1)."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.job import Job, JobStatus
from app.schemas.job import JobOut
from app.storage.local import LocalStorage, get_storage

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
}
ALLOWED_EXTENSIONS = {ext for exts in ALLOWED_CONTENT_TYPES.values() for ext in exts}


def _extension_for(filename: str, content_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in ALLOWED_EXTENSIONS:
        return suffix
    for mime, exts in ALLOWED_CONTENT_TYPES.items():
        if mime == content_type:
            return next(iter(exts))
    return ".png"


def _safe_filename(filename: str, content_type: str) -> str:
    stem = Path(filename).stem or "image"
    return f"{stem}{_extension_for(filename, content_type)}"


def validate_and_read_image(upload: UploadFile, settings: Settings) -> tuple[bytes, str, str]:
    filename = upload.filename or "upload"
    content_type = (upload.content_type or "").lower().strip()

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload JPG, JPEG, PNG or WEBP.",
        )

    data = upload.file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file.")
    if len(data) > settings.max_upload_bytes:
        max_mb = settings.max_upload_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {max_mb:.0f} MB.",
        )

    try:
        with Image.open(BytesIO(data)) as img:
            img.verify()
        # Re-open after verify (Pillow requirement)
        with Image.open(BytesIO(data)) as img:
            fmt = (img.format or "").upper()
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read image. File may be corrupted.",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read image. File may be corrupted.",
        ) from exc

    expected = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    if fmt not in expected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format. Please upload JPG, JPEG, PNG or WEBP.",
        )
    content_type = expected[fmt]
    return data, _safe_filename(filename, content_type), content_type


def to_job_out(job: Job, storage: LocalStorage) -> JobOut:
    prepared_url = storage.public_url_path(job.prepared_key) if job.prepared_key else None
    return JobOut(
        id=job.id,
        status=job.status,
        original_filename=job.original_filename,
        content_type=job.content_type,
        original_url=storage.public_url_path(job.original_key),
        current_url=storage.public_url_path(job.current_key),
        prepared_url=prepared_url,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def create_job_from_upload(
    db: Session,
    upload: UploadFile,
    settings: Settings | None = None,
    storage: LocalStorage | None = None,
) -> JobOut:
    cfg = settings or get_settings()
    store = storage or get_storage(cfg)

    data, filename, content_type = validate_and_read_image(upload, cfg)

    job = Job(
        status=JobStatus.uploaded,
        original_filename=filename,
        content_type=content_type,
        original_key="",
        current_key="",
    )
    db.add(job)
    db.flush()

    key = store.make_key("originals", filename, job.id)
    store.save_bytes(key, data)
    job.original_key = key
    job.current_key = key
    db.commit()
    db.refresh(job)

    logger.info("Created job %s from %s", job.id, filename)
    return to_job_out(job, store)


def get_job(db: Session, job_id: str, storage: LocalStorage | None = None) -> JobOut:
    store = storage or get_storage()
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return to_job_out(job, store)
