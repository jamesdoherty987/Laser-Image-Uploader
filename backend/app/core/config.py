from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    secret_key: str = "dev-secret-change-me"
    environment: str = "development"
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    database_url: str = "sqlite:///./laser.db"
    storage_dir: str = "./uploads"
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    openai_api_key: str = ""
    gemini_api_key: str = ""
    image_edit_model: str = "gpt-image-1"
    gemini_image_model: str = "gemini-2.5-flash-image"
    # gemini | openai | auto (prefer gemini when keyed)
    image_edit_provider: str = "auto"

    desktop_pairing_token: str = ""
    cors_extra_origins: str = ""

    admin_username: str = "admin"
    admin_password: str = "galvin-admin"

    @field_validator("frontend_url", "backend_url", mode="before")
    @classmethod
    def _strip_trailing_slash(cls, v: object) -> object:
        if isinstance(v, str):
            return v.rstrip("/")
        return v

    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        return path

    def cors_origins(self) -> list[str]:
        origins = [
            self.frontend_url,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
        extra = [o.strip() for o in self.cors_extra_origins.split(",") if o.strip()]
        # Preserve order, drop duplicates
        seen: set[str] = set()
        result: list[str] = []
        for origin in origins + extra:
            if origin not in seen:
                seen.add(origin)
                result.append(origin)
        return result


@lru_cache
def get_settings() -> Settings:
    return Settings()
