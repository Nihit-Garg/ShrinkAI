"""
Context Assembler — Week 3+4: Intent-aware context assembly.

Passes user_message through to rag_pipeline.build_basic_context()
so episodic retrieval can use it as the query vector.
"""
import logging
from typing import Optional
from app.db_client import SupabaseDB
from app.services.rag_pipeline import build_basic_context

logger = logging.getLogger(__name__)

INTENT_TYPES = ["venting", "seeking_advice", "crisis", "casual", "reflecting"]


def assemble_context(
    user_id: str,
    session_id: str,
    db: SupabaseDB,
    user_message: Optional[str] = None,
) -> dict[str, str]:
    """
    Builds the context dict for the LLM call.

    user_message is forwarded as the retrieval query so Layer 3
    (episodic cross-session retrieval) can find semantically relevant
    past moments.

    Week 4 intent routing: classify_intent() always returns 'casual' for now.
    Full intent-aware retrieval strategy routing is post-Week 4.
    """
    return build_basic_context(user_id, session_id, db, user_message=user_message)


def classify_intent(message: str) -> str:
    """
    STUB — Week 4.
    Classifies user message intent for retrieval strategy selection.
    Returns one of: venting, seeking_advice, crisis, casual, reflecting.
    """
    # TODO (Week 4): Replace with Gemini Flash intent classification call
    return "casual"
