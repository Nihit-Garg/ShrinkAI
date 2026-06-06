"""Mood router — wired to real Supabase data."""
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.db_client import SupabaseDB, get_db

router = APIRouter(prefix="/mood", tags=["Mood"])


@router.get("/trend")
async def mood_trend(
    limit: int = 30,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
):
    """
    Return the last `limit` mood entries for the current user in chronological order.
    Each entry has: score (-1.0 to 1.0), recorded_at (ISO string), session_id.
    """
    user_id = current_user["user_id"]
    entries = db.get_mood_trend(user_id, limit=limit)
    return {"entries": entries}
