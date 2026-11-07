from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.job import JobStatus


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: JobStatus
    original_filename: str
    content_type: str
    original_url: str
    current_url: str
    prepared_url: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class JobStatusOut(BaseModel):
    id: str
    status: JobStatus
    error_message: str | None = None
