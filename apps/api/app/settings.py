from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Local: apps/api/app/settings.py → repo root `.env`. Hosted image is
# /app/app/settings.py (shallower) — skip the file; process env / secrets win.
_parents = Path(__file__).resolve().parents
_REPO_ENV_FILE = _parents[3] / ".env" if len(_parents) > 3 else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_REPO_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    audit_actor: str = "demo-operator"
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    # Worker / API ops logs (stdlib + structlog). Not the product audit trail.
    log_level: str = "INFO"

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
