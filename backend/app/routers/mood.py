"""Mood router — STUB. Week 5 implementation."""
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/mood", tags=["Mood"])


@router.get("/trend")
async def mood_trend(current_user: dict = Depends(get_current_user)):
    """STUB — Week 5. Returns time-series mood scores for the current user."""
    return {"message": "Mood trend endpoint — coming in Week 5.", "entries": []}
