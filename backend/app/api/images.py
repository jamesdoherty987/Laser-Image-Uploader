import logging

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job import EditPrompt, JobOut, JobStatusOut, PrepareOptions, RevertRequest
from app.services import images as image_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/", response_model=list[JobOut])
def list_images(
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[JobOut]:
    """Recent jobs for the studio session list."""
    return image_service.list_recent_jobs(db, limit=limit)


@router.post("/upload", response_model=JobOut)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> JobOut:
    """Accept an image and return a job with preview URLs."""
    return image_service.create_job_from_upload(db, file)


@router.get("/{job_id}", response_model=JobOut)
def get_image(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    return image_service.get_job(db, job_id)


@router.get("/{job_id}/status", response_model=JobStatusOut)
def get_image_status(job_id: str, db: Session = Depends(get_db)) -> JobStatusOut:
    job = image_service.get_job(db, job_id)
    return JobStatusOut(id=job.id, status=job.status, error_message=job.error_message)


@router.post("/{job_id}/prepare", response_model=JobOut)
def prepare_image(
    job_id: str,
    options: PrepareOptions | None = None,
    live: bool = Query(False, description="Quiet live-preview re-prep (no status flicker)"),
    db: Session = Depends(get_db),
) -> JobOut:
    """Run the laser preparation pipeline (contrast, dither, threshold, etc.)."""
    return image_service.prepare_job(db, job_id, options=options, live=live)


@router.post("/{job_id}/edit", response_model=JobOut)
def edit_image(
    job_id: str,
    payload: EditPrompt,
    db: Session = Depends(get_db),
) -> JobOut:
    """AI edit via Gemini (preferred) or OpenAI."""
    return image_service.edit_job(db, job_id, payload)


@router.post("/{job_id}/revert", response_model=JobOut)
def revert_image(
    job_id: str,
    payload: RevertRequest,
    db: Session = Depends(get_db),
) -> JobOut:
    """Undo the last AI edit, or restore the original upload."""
    return image_service.revert_job(db, job_id, payload)


@router.delete("/{job_id}", status_code=204)
def delete_image(job_id: str, db: Session = Depends(get_db)) -> None:
    """Remove a job and its stored image files from Recent."""
    image_service.delete_job(db, job_id)
