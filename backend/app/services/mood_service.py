"""
Mood Service — Week 5 implementation.
Extracts sentiment score from session and stores in mood_entries.

TODO (Week 5):
- Run sentiment analysis on completed session transcript
- Store score in mood_entries table
- Aggregate scores for trend visualization
"""
import logging

logger = logging.getLogger(__name__)


def extract_session_mood(session_transcript: str) -> float:
    """
    STUB — Week 5.
    Returns a sentiment score from -1.0 (very negative) to 1.0 (very positive).
    Will be extracted from the reflection prompt output JSON.
    """
    return 0.0


def get_mood_trend(user_id: str, limit: int = 30) -> list[dict]:
    """STUB — Week 5. Returns time-series mood data for a user."""
    return []
