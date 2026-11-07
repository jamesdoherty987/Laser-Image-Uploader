from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    # Import models so metadata is registered
    from app import models  # noqa: F401
    from app.services.content import ensure_contact
    from app.services.seed_shop import seed_example_products

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()
    db = SessionLocal()
    try:
        seed_example_products(db)
        ensure_contact(db)
    finally:
        db.close()


def _ensure_sqlite_columns() -> None:
    """Add columns introduced after first create_all (SQLite has no migrations)."""
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(jobs)").fetchall()
        existing = {row[1] for row in rows}
        if "edited_key" not in existing:
            conn.exec_driver_sql("ALTER TABLE jobs ADD COLUMN edited_key VARCHAR(512)")
        if "edit_history" not in existing:
            conn.exec_driver_sql("ALTER TABLE jobs ADD COLUMN edit_history TEXT")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
