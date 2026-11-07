"""Desktop connector API — pull ready jobs with pairing token."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.desktop_auth import require_desktop
from app.db.session import get_db
from app.models.job import JobStatus
from app.schemas.job import DesktopFailIn, JobOut
from app.services import images as image_service

router = APIRouter(
    prefix="/desktop",
    tags=["desktop"],
    dependencies=[Depends(require_desktop)],
)


@router.get("/jobs", response_model=list[JobOut])
def desktop_list_jobs(
    status: JobStatus = Query(default=JobStatus.ready),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[JobOut]:
    return image_service.list_recent_jobs(db, limit=limit, max_limit=100, status=status)


@router.post("/jobs/{job_id}/claim", response_model=JobOut)
def desktop_claim_job(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    job = image_service.get_job(db, job_id)
    if job.status not in {JobStatus.ready, JobStatus.downloading}:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=f"Job is {job.status.value}, not ready to claim.")
    return image_service.update_job_status(db, job_id, new_status=JobStatus.downloading)


@router.post("/jobs/{job_id}/imported", response_model=JobOut)
def desktop_mark_imported(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    return image_service.update_job_status(db, job_id, new_status=JobStatus.imported)


@router.post("/jobs/{job_id}/failed", response_model=JobOut)
def desktop_mark_failed(
    job_id: str,
    payload: DesktopFailIn,
    db: Session = Depends(get_db),
) -> JobOut:
    return image_service.update_job_status(
        db,
        job_id,
        new_status=JobStatus.failed,
        error_message=payload.error_message,
    )
