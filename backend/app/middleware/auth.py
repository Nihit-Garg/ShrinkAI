"""
Auth middleware — JWT verification via Supabase with in-memory token cache.

Every protected endpoint calls get_current_user(), which validates the Bearer JWT.
Without caching, each request makes a round-trip to Supabase's auth API — under
concurrent load this serialises requests and hammers the Supabase rate limits.

The cache stores validated tokens for 60 seconds. A user's first request in any
60-second window hits Supabase; subsequent requests are served instantly from cache.
"""
import logging
import time
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()

# ── Simple in-memory token cache ──────────────────────────────────────────────
# Format: { token_str: (user_dict, expires_timestamp) }
_TOKEN_CACHE: dict[str, tuple[dict, float]] = {}
_TOKEN_TTL_SECONDS = 60  # Re-validate with Supabase every 60s


def _get_cached(token: str) -> Optional[dict]:
    entry = _TOKEN_CACHE.get(token)
    if entry:
        user, expires_at = entry
        if time.monotonic() < expires_at:
            return user
        del _TOKEN_CACHE[token]   # Expired — remove
    return None


def _set_cached(token: str, user: dict) -> None:
    _TOKEN_CACHE[token] = (user, time.monotonic() + _TOKEN_TTL_SECONDS)
    # Evict expired entries if cache grows large (safety valve)
    if len(_TOKEN_CACHE) > 1000:
        now = time.monotonic()
        expired_keys = [k for k, (_, exp) in _TOKEN_CACHE.items() if exp < now]
        for k in expired_keys:
            del _TOKEN_CACHE[k]


# ── Dependency ─────────────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency.
    Verifies the Bearer JWT with Supabase (or returns cached result).
    Raises HTTP 401 if the token is invalid or expired.
    """
    token = credentials.credentials

    # Fast path — return cached result
    cached = _get_cached(token)
    if cached:
        return cached

    # Slow path — validate with Supabase
    try:
        supabase = get_supabase_admin()
        response = supabase.auth.get_user(token)
        user = response.user
        if user is None:
            raise ValueError("No user returned from Supabase")

        user_dict = {"user_id": user.id, "email": user.email}
        _set_cached(token, user_dict)
        return user_dict

    except Exception as e:
        logger.warning(f"Auth failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
