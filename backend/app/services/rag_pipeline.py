"""
RAG Pipeline Service — Week 3+4: Full hybrid retrieval with cross-encoder reranking.

Context assembly pipeline:
  Layer 1 (Static):  Identity profile narrative from Supabase
  Layer 2 (Current): Last 20 messages from the current session
  Layer 3 (Dynamic): Top-4 episodic moments from past sessions
                     retrieved via hybrid BM25+dense search + cross-encoder reranking

Layer 3 is what makes the AI feel like it remembers you across sessions.
"""
import logging
from typing import Optional
from app.db_client import SupabaseDB
from app.services.questionnaire_service import get_profile_narrative

logger = logging.getLogger(__name__)

MAX_RECENT_MESSAGES = 20


def _format_episodic_moments(moments: list[dict]) -> str:
    """Format retrieved episodic chunks into readable context for the system prompt."""
    if not moments:
        return "No relevant past moments retrieved yet — this may be the user's first or second session."

    lines = ["These specific moments from past sessions are relevant to what the user is sharing now:\n"]
    for i, m in enumerate(moments, 1):
        lines.append(f"{i}. {m['document']}")
    return "\n".join(lines)


def build_basic_context(
    user_id: str,
    session_id: str,
    db: SupabaseDB,
    user_message: Optional[str] = None,
) -> dict[str, str]:
    """
    Full Week 3+4 context assembly:
      - identity_profile:      LLM-generated profile narrative
      - recent_sessions:       last 20 messages from current session
      - relevant_past_moments: hybrid-retrieved + reranked episodic chunks

    user_message is used as the retrieval query for past moments.
    If not provided (e.g. first message of session), we skip episodic retrieval.
    """
    # ── Layer 1: Identity profile ──────────────────────────────────────────────
    narrative = get_profile_narrative(user_id, db)
    identity_profile = narrative or "No profile available yet. This is the user's first session."

    # ── Layer 2: Current session messages ──────────────────────────────────────
    recent_messages = db.get_session_messages(session_id, limit=MAX_RECENT_MESSAGES)
    if recent_messages:
        transcript_lines = [
            f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages
        ]
        recent_sessions = "\n".join(transcript_lines)
    else:
        recent_sessions = "This is the start of the current session."

    # ── Layer 3: Cross-session episodic retrieval ──────────────────────────────
    relevant_past_moments = "No relevant past moments retrieved yet — this may be the user's first session."

    if user_message:
        try:
            from app.services.hybrid_retriever import hybrid_retrieve
            from app.services.reranker import rerank

            # Stage 1: Hybrid BM25 + dense retrieval → top-10 candidates
            candidates = hybrid_retrieve(user_id, user_message, top_n=10)

            if candidates:
                # Stage 2: Cross-encoder reranking → top-4
                top_moments = rerank(user_message, candidates, top_k=4)
                relevant_past_moments = _format_episodic_moments(top_moments)
                logger.info(
                    f"Episodic retrieval: {len(candidates)} candidates → "
                    f"{len(top_moments)} after reranking for user {user_id}"
                )
            else:
                logger.debug(f"No episodic chunks available yet for user {user_id}")

        except Exception as e:
            logger.warning(f"Episodic retrieval failed (non-fatal): {e}")

    return {
        "identity_profile": identity_profile,
        "recent_sessions": recent_sessions,
        "relevant_past_moments": relevant_past_moments,
    }
