from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./medannotate.db"
    storage_dir: str = "data/uploads"
    model_path: str | None = None
    allow_demo_mode: bool = True
    model_input_size: int = 256
    threshold: float = 0.5
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MEDANNOTATE_",
        extra="ignore",
    )

    @property
    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
