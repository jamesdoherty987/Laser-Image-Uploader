"""Admin endpoints for the customer job inbox and desktop connector."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.admin_auth import require_admin
from app.core.config import Settings, get_settings
from app.core.desktop_auth import ensure_pairing_token
from app.db.session import get_db
from app.models.job import JobStatus
from app.schemas.job import DesktopInfoOut, JobOut, JobStatusUpdate, PrepareOptions
from app.services import images as image_service
from app.services.desktop_package import build_desktop_zip

router = APIRouter(prefix="/admin", tags=["admin-jobs"], dependencies=[Depends(require_admin)])


@router.get("/jobs", response_model=list[JobOut])
def admin_list_jobs(
    limit: int = Query(100, ge=1, le=500),
    status: JobStatus | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[JobOut]:
    """All customer uploads for the laser operator."""
    return image_service.list_recent_jobs(db, limit=limit, max_limit=500, status=status)


@router.get("/jobs/{job_id}", response_model=JobOut)
def admin_get_job(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    return image_service.get_job(db, job_id)


@router.post("/jobs/{job_id}/prepare", response_model=JobOut)
def admin_prepare_job(
    job_id: str,
    options: PrepareOptions | None = None,
    db: Session = Depends(get_db),
) -> JobOut:
    return image_service.prepare_job(db, job_id, options=options)


@router.patch("/jobs/{job_id}/status", response_model=JobOut)
def admin_update_job_status(
    job_id: str,
    payload: JobStatusUpdate,
    db: Session = Depends(get_db),
) -> JobOut:
    return image_service.update_job_status(
        db,
        job_id,
        new_status=payload.status,
        error_message=payload.error_message,
    )


@router.delete("/jobs/{job_id}")
def admin_delete_job(job_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    image_service.delete_job(db, job_id)
    return {"status": "deleted"}


@router.get("/desktop", response_model=DesktopInfoOut)
def admin_desktop_info(settings: Settings = Depends(get_settings)) -> DesktopInfoOut:
    token = ensure_pairing_token(settings)
    return DesktopInfoOut(
        pairing_token=token,
        api_base=settings.backend_url,
        download_path="/api/admin/desktop/download",
        instructions=(
            "Download the zip, unzip on the Windows PC next to the laser, "
            "run run_connector.bat (or python main.py --setup), and paste this pairing token."
        ),
    )


@router.get("/desktop/download")
def admin_desktop_download() -> Response:
    data = build_desktop_zip()
    return Response(
        content=data,
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="galvin-crafts-desktop.zip"',
        },
    )
