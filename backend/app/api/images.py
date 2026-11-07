import logging

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job import JobOut, JobStatusOut
from app.services import images as image_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/upload", response_model=JobOut)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> JobOut:
    """Stage 1: accept an image and return a job with preview URLs."""
    return image_service.create_job_from_upload(db, file)


@router.get("/{job_id}", response_model=JobOut)
def get_image(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    return image_service.get_job(db, job_id)


@router.get("/{job_id}/status", response_model=JobStatusOut)
def get_image_status(job_id: str, db: Session = Depends(get_db)) -> JobStatusOut:
    job = image_service.get_job(db, job_id)
    return JobStatusOut(id=job.id, status=job.status, error_message=job.error_message)
