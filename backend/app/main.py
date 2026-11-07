import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import admin_jobs, content, desktop, images
from app.core.config import get_settings
from app.core.desktop_auth import ensure_pairing_token
from app.db.session import init_db
from app.storage.local import get_storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()
storage = get_storage(settings)
UPLOAD_DIR = storage.root
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    logger.info("Storage root: %s", UPLOAD_DIR)
    token = ensure_pairing_token(settings)
    logger.info("Desktop pairing token ready (%s…)", token[:6])
    if settings.is_production() and settings.secret_key in {
        "",
        "dev-secret-change-me",
        "change-me-to-a-long-random-string",
    }:
        logger.warning("SECRET_KEY is still a default value; set a long random secret.")
    yield


app = FastAPI(
    title="Laser Image Uploader API",
    version="0.1.0",
    description="Upload, AI-edit, and prepare images for laser engraving",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.include_router(images.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(content.admin_router, prefix="/api")
app.include_router(admin_jobs.router, prefix="/api")
app.include_router(desktop.router, prefix="/api")


@app.get("/")
def root() -> RedirectResponse:
    """API has no UI — send browsers to the Vite frontend."""
    return RedirectResponse(url=settings.frontend_url, status_code=307)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
