"""
Memory router — Week 3+4 implementation.

Endpoints:
  GET /memory/mood-trend     — last N mood scores with direction analysis
  GET /memory/profile        — user's current profile (narrative + structured)
  GET /memory/episodes       — count of episodic chunks stored in ChromaDB
  POST /memory/reflect/{session_id} — manually trigger reflection for a session
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from app.db_client import SupabaseDB, get_db
from app.middleware.auth import get_current_user
from app.vector_store import get_episodic_collection
from app.services.memory_service import run_post_session_reflection
from app.services.questionnaire_service import get_profile_narrative, get_structured_profile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/mood-trend")
async def get_mood_trend(
    limit: int = 30,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
):
    """
    Returns the user's mood score history and overall trend direction.

    Scores are on a scale from -1.0 (very distressed) to +1.0 (very positive),
    extracted from post-session reflection by the LLM.
    """
    user_id = current_user["user_id"]
    trend = db.get_mood_trend(user_id, limit=limit)

    if not trend:
        return {
            "trend": [],
            "direction": "unknown",
            "message": "No mood data yet — complete a few sessions first.",
        }

    scores = [entry["score"] for entry in trend]

    # Simple trend direction: compare first half average to second half average
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
        delta = second_half_avg - first_half_avg
        if delta > 0.1:
            direction = "improving"
        elif delta < -0.1:
            direction = "declining"
        else:
            direction = "stable"
    else:
        direction = "insufficient_data"

    return {
        "trend": trend,
        "direction": direction,
        "latest_score": scores[-1] if scores else None,
        "average_score": round(sum(scores) / len(scores), 2),
    }


@router.get("/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
):
    """Returns the user's current psychological profile: narrative + 5 structured dimensions."""
    user_id = current_user["user_id"]
    narrative = get_profile_narrative(user_id, db)
    structured = get_structured_profile(user_id, db)

    if not narrative:
        raise HTTPException(status_code=404, detail="Profile not found. Complete the questionnaire first.")

    return {
        "narrative": narrative,
        "structured_profile": structured,
    }


@router.get("/episodes")
async def get_episode_count(
    current_user: dict = Depends(get_current_user),
):
    """Returns how many episodic memory chunks have been stored for this user."""
    user_id = current_user["user_id"]
    try:
        collection = get_episodic_collection(user_id)
        count = collection.count()
    except Exception:
        count = 0

    return {
        "episode_count": count,
        "message": f"{count} episodic memory chunk{'s' if count != 1 else ''} stored.",
    }


@router.post("/reflect/{session_id}")
async def trigger_reflection(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
):
    """
    Manually trigger post-session reflection for a given session.
    Useful for testing or re-running a failed reflection.
    """
    user_id = current_user["user_id"]
    session = db.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Force reset reflection_done so it can run again
    db.update_session(session_id, {"reflection_done": False})

    reflection = run_post_session_reflection(user_id, session_id, db)

    if not reflection:
        return {"message": "Reflection skipped — insufficient messages or already done.", "session_id": session_id}

    return {
        "message": "Reflection completed.",
        "session_id": session_id,
        "key_moments_stored": len(reflection.get("key_moments", [])),
        "mood_score": reflection.get("mood_score"),
    }
