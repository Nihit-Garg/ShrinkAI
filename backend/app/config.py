"""
Application configuration loaded from environment variables.
All settings are defined here — no raw os.getenv() calls anywhere else in the codebase.
"""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env from the project root regardless of CWD
# backend/app/config.py → parent → backend/ → parent → project root
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # ── LLMs ────────────────────────────────────────────────────────────────
    gemini_api_key: str
    groq_api_key: str

    # ── Supabase (REST + Auth) ───────────────────────────────────────────────
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # ── PostgreSQL via SQLAlchemy ────────────────────────────────────────────
    # Get this from Supabase Dashboard → Settings → Database → Connection string
    # Format: postgresql://postgres.[ref]:[password]@[host]:5432/postgres
    database_url: str

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_db"

    # ── App ──────────────────────────────────────────────────────────────────
    secret_key: str = "change-this-in-production"
    env: str = "development"
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — created once per process."""
    return Settings()
