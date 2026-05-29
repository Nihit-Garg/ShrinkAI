"""
Auth middleware — JWT verification via Supabase.
FastAPI dependency: inject `current_user` into any route that requires authentication.
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency.
    Verifies the Bearer JWT with Supabase and returns the user dict.
    Raises HTTP 401 if the token is invalid or expired.
    """
    token = credentials.credentials
    try:
        supabase = get_supabase_admin()
        response = supabase.auth.get_user(token)
        user = response.user
        if user is None:
            raise ValueError("No user returned from Supabase")
        return {"user_id": user.id, "email": user.email}
    except Exception as e:
        logger.warning(f"Auth failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
