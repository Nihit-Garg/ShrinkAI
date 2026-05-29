"""
Supabase client — used ONLY for Auth operations (signup, login, JWT verification).
All table reads/writes go through SQLAlchemy (database.py).
"""
from functools import lru_cache
from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()


@lru_cache()
def get_supabase() -> Client:
    """Public anon client — used for user-facing auth flows."""
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache()
def get_supabase_admin() -> Client:
    """Service role client — server-side only, never exposed to frontend."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
