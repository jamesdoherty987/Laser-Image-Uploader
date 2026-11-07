"""Image upload, laser preparation, and job helpers."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.image_processing.laser import prepare_for_laser
from app.models.job import Job, JobStatus
from app.schemas.job import EditPrompt, JobOut, PrepareOptions, RevertRequest
from app.services.ai_edit import edit_image
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


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


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


def _source_key(job: Job) -> str | None:
    """Prefer AI edit, then current (if not prepared), then original upload."""
    if job.edited_key:
        return job.edited_key
    if job.current_key and job.current_key != job.prepared_key:
        return job.current_key
    return job.original_key or None


def _edit_history(job: Job) -> list[str]:
    raw = (job.edit_history or "").strip()
    if not raw:
        # Back-compat: single edited_key with no history recorded yet
        return [job.edited_key] if job.edited_key else []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return [job.edited_key] if job.edited_key else []
    if not isinstance(data, list):
        return [job.edited_key] if job.edited_key else []
    return [str(item) for item in data if item]


def _set_edit_history(job: Job, keys: list[str]) -> None:
    job.edit_history = json.dumps(keys) if keys else None
    job.edited_key = keys[-1] if keys else None


def _metrics_for_job(
    job: Job, storage: LocalStorage
) -> tuple[int | None, int | None, int | None, float | None, float | None]:
    key = job.prepared_key or job.edited_key or job.current_key or job.original_key
    if not key or not storage.exists(key):
        return None, None, None, None, None
    try:
        data = storage.read_bytes(key)
        with Image.open(BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            width, height = image.size
            dpi_info = image.info.get("dpi")
            dpi: int | None = None
            if isinstance(dpi_info, tuple) and dpi_info and dpi_info[0]:
                dpi = int(round(float(dpi_info[0])))
            elif isinstance(dpi_info, (int, float)) and dpi_info:
                dpi = int(round(float(dpi_info)))
            width_mm = round(width / dpi * 25.4, 2) if dpi else None
            height_mm = round(height / dpi * 25.4, 2) if dpi else None
            return width, height, dpi, width_mm, height_mm
    except OSError:
        logger.warning("Could not read dimensions for job %s", job.id)
        return None, None, None, None, None


def to_job_out(job: Job, storage: LocalStorage) -> JobOut:
    history = _edit_history(job)
    edited_url = storage.public_url_path(job.edited_key) if job.edited_key else None
    prepared_url = storage.public_url_path(job.prepared_key) if job.prepared_key else None
    width, height, dpi, width_mm, height_mm = _metrics_for_job(job, storage)
    return JobOut(
        id=job.id,
        status=job.status,
        original_filename=job.original_filename,
        content_type=job.content_type,
        original_url=storage.public_url_path(job.original_key),
        current_url=storage.public_url_path(job.current_key),
        edited_url=edited_url,
        prepared_url=prepared_url,
        error_message=job.error_message,
        width=width,
        height=height,
        dpi=dpi,
        width_mm=width_mm,
        height_mm=height_mm,
        edit_count=len(history),
        can_undo_edit=len(history) > 0,
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


def prepare_job(
    db: Session,
    job_id: str,
    options: PrepareOptions | None = None,
    storage: LocalStorage | None = None,
    *,
    live: bool = False,
) -> JobOut:
    store = storage or get_storage()
    opts = options or PrepareOptions()
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    source_key = _source_key(job)
    if not source_key or not store.exists(source_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job has no image to prepare.",
        )

    if not live:
        job.status = JobStatus.preparing
        job.error_message = None
        job.updated_at = _utcnow()
        db.commit()

    try:
        source = store.read_bytes(source_key)
        prepared_bytes, _, _, _metrics = prepare_for_laser(
            source,
            mode=opts.mode,  # type: ignore[arg-type]
            contrast=opts.contrast,
            brightness=opts.brightness,
            sharpness=opts.sharpness,
            denoise=opts.denoise,
            invert=opts.invert,
            threshold=opts.threshold,
            width_mm=opts.width_mm,
            height_mm=opts.height_mm,
            dpi=opts.dpi,
        )
        prepared_name = f"{Path(job.original_filename).stem}-laser.png"
        prepared_key = store.make_key("prepared", prepared_name, job.id)
        store.save_bytes(prepared_key, prepared_bytes)

        job.prepared_key = prepared_key
        job.current_key = prepared_key
        job.status = JobStatus.ready
        job.error_message = None
        job.updated_at = _utcnow()
        db.commit()
        db.refresh(job)
        logger.info("Prepared job %s for laser (%s)", job.id, opts.mode)
        return to_job_out(job, store)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 — surface as failed job state
        logger.exception("Failed to prepare job %s", job_id)
        if not live:
            job.status = JobStatus.failed
            job.error_message = "Could not prepare this image for laser engraving."
            job.updated_at = _utcnow()
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not prepare this image for laser engraving.",
        ) from exc


def edit_job(
    db: Session,
    job_id: str,
    payload: EditPrompt,
    storage: LocalStorage | None = None,
    settings: Settings | None = None,
) -> JobOut:
    cfg = settings or get_settings()
    store = storage or get_storage(cfg)
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    source_key = _source_key(job)
    if not source_key or not store.exists(source_key):
        raise HTTPException(status_code=400, detail="Job has no image to edit.")

    job.status = JobStatus.editing
    job.error_message = None
    job.updated_at = _utcnow()
    db.commit()

    try:
        source = store.read_bytes(source_key)
        edited_bytes = edit_image(cfg, source, payload.prompt)
        history = _edit_history(job)
        step = len(history) + 1
        edited_name = f"{Path(job.original_filename).stem}-edit-{step}.png"
        edited_key = store.make_key("edited", edited_name, job.id)
        store.save_bytes(edited_key, edited_bytes)
        history.append(edited_key)
        _set_edit_history(job, history)
        job.current_key = edited_key
        job.prepared_key = None
        job.status = JobStatus.edited
        job.updated_at = _utcnow()
        db.commit()
        db.refresh(job)
        logger.info("Edited job %s via AI (step %s)", job.id, step)
        return to_job_out(job, store)
    except HTTPException as exc:
        job.status = JobStatus.failed
        job.error_message = str(exc.detail)
        job.updated_at = _utcnow()
        db.commit()
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to edit job %s", job_id)
        job.status = JobStatus.failed
        job.error_message = "AI edit failed."
        job.updated_at = _utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail=job.error_message) from exc


def revert_job(
    db: Session,
    job_id: str,
    payload: RevertRequest,
    storage: LocalStorage | None = None,
) -> JobOut:
    """Undo the last AI edit, or restore the original upload."""
    store = storage or get_storage()
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    history = _edit_history(job)
    if payload.target == "original":
        if not history and not job.edited_key and not job.prepared_key:
            raise HTTPException(status_code=400, detail="Nothing to revert.")
        _set_edit_history(job, [])
        job.current_key = job.original_key
        job.prepared_key = None
        job.status = JobStatus.uploaded
        job.error_message = None
        job.updated_at = _utcnow()
        db.commit()
        db.refresh(job)
        logger.info("Reverted job %s to original", job.id)
        return to_job_out(job, store)

    # previous AI edit
    if not history:
        raise HTTPException(status_code=400, detail="No AI edits to undo.")
    history = history[:-1]
    _set_edit_history(job, history)
    if history:
        job.current_key = history[-1]
        job.status = JobStatus.edited
    else:
        job.current_key = job.original_key
        job.status = JobStatus.uploaded
    job.prepared_key = None
    job.error_message = None
    job.updated_at = _utcnow()
    db.commit()
    db.refresh(job)
    logger.info("Undid last AI edit on job %s (%s left)", job.id, len(history))
    return to_job_out(job, store)


def list_recent_jobs(
    db: Session,
    *,
    limit: int = 8,
    max_limit: int = 20,
    status: JobStatus | str | None = None,
    storage: LocalStorage | None = None,
) -> list[JobOut]:
    store = storage or get_storage()
    query = db.query(Job)
    if status is not None:
        status_value = status if isinstance(status, JobStatus) else JobStatus(status)
        query = query.filter(Job.status == status_value)
    rows = (
        query.order_by(Job.created_at.desc())
        .limit(max(1, min(limit, max_limit)))
        .all()
    )
    return [to_job_out(job, store) for job in rows]


def update_job_status(
    db: Session,
    job_id: str,
    *,
    new_status: JobStatus,
    error_message: str | None = None,
    storage: LocalStorage | None = None,
) -> JobOut:
    store = storage or get_storage()
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    job.status = new_status
    if error_message is not None:
        job.error_message = error_message
    elif new_status != JobStatus.failed:
        job.error_message = None
    job.updated_at = _utcnow()
    db.commit()
    db.refresh(job)
    return to_job_out(job, store)


def delete_job(db: Session, job_id: str, storage: LocalStorage | None = None) -> None:
    store = storage or get_storage()
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    keys = {
        job.original_key,
        job.current_key,
        job.edited_key,
        job.prepared_key,
        *_edit_history(job),
    }
    for key in keys:
        if not key:
            continue
        try:
            if store.exists(key):
                store.delete(key)
        except (OSError, ValueError):
            logger.warning("Could not delete storage key %s for job %s", key, job_id)
    db.delete(job)
    db.commit()
    logger.info("Deleted job %s", job_id)
