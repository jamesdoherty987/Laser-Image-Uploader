import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class JobStatus(str, enum.Enum):
    uploaded = "uploaded"
    editing = "editing"
    edited = "edited"
    preparing = "preparing"
    ready = "ready"
    downloading = "downloading"
    imported = "imported"
    failed = "failed"


class Job(Base):
    """One customer image workflow from upload through CorelDRAW import."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False),
        default=JobStatus.uploaded,
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Storage keys (relative paths) — swap for object-store keys later
    original_key: Mapped[str] = mapped_column(String(512), nullable=False)
    current_key: Mapped[str] = mapped_column(String(512), nullable=False)
    prepared_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
    )
