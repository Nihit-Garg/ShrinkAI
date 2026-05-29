"""
Memory Service — Full agentic post-session reflection pipeline.

This is the "self-learning" loop that makes Shrink AI improve over time.

After each session (triggered automatically after the 5th message, or explicitly
via /conversation/end-session), an LLM call analyses the full transcript and:

  1. Extracts key_moments → embedded individually in ChromaDB episodic collection
  2. Extracts mood_score → stored in Supabase mood_entries
  3. Stores the full reflection JSON in Supabase sessions.reflection_json
  4. Invalidates the BM25 cache so the next query picks up new chunks
  5. Optionally flags if the user's profile narrative needs updating

The 'agentic' pattern here: the LLM is not just answering a question —
it is reasoning about its own conversation history, deciding what to remember,
and autonomously updating its long-term memory store. This mirrors the
Reflect-Act-Observe loop in agent frameworks.
"""
import logging
import uuid
from typing import Optional

from app.db_client import SupabaseDB
from app.services.llm_service import get_llm_service
from app.vector_store import get_episodic_collection, get_embedder
from app.services.bm25_store import invalidate_cache
from app.prompts.reflection_prompt import build_reflection_prompt
from app.services.questionnaire_service import get_profile_narrative

logger = logging.getLogger(__name__)

# Minimum messages needed before reflection is worth running
MIN_MESSAGES_FOR_REFLECTION = 4


def _build_transcript(messages: list[dict]) -> str:
    """Format message list into a clean transcript string for the reflection LLM."""
    lines = []
    for msg in messages:
        role = "You" if msg["role"] == "assistant" else "User"
        lines.append(f"{role}: {msg['content']}")
    return "\n\n".join(lines)


def _store_episodic_chunks(
    user_id: str,
    session_id: str,
    key_moments: list[str],
) -> list[str]:
    """
    Embed each key_moment individually and store in ChromaDB episodic collection.

    Each moment gets its own vector so it can be retrieved independently
    based on semantic relevance to future queries.

    Returns list of stored chunk IDs.
    """
    if not key_moments:
        return []

    collection = get_episodic_collection(user_id)
    embedder = get_embedder()
    chunk_ids = []

    for i, moment in enumerate(key_moments):
        if not moment or not moment.strip():
            continue

        chunk_id = f"episodic_{user_id}_{session_id}_{i}"
        embedding = embedder.embed_document(moment)

        collection.upsert(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[moment],
            metadatas=[{
                "user_id": user_id,
                "session_id": session_id,
                "chunk_index": i,
                "type": "episodic_moment",
            }],
        )
        chunk_ids.append(chunk_id)

    logger.info(
        f"Stored {len(chunk_ids)} episodic chunks in ChromaDB "
        f"for user {user_id}, session {session_id}"
    )
    return chunk_ids


def run_post_session_reflection(user_id: str, session_id: str, db: SupabaseDB) -> dict:
    """
    Full agentic post-session reflection pipeline.

    Steps:
      1. Load the session transcript from Supabase
      2. Load the user's current profile narrative
      3. Run the reflection LLM prompt
      4. Store key_moments as episodic chunks in ChromaDB
      5. Store mood_score in mood_entries
      6. Store full reflection JSON in sessions.reflection_json
      7. Invalidate BM25 cache so new chunks are picked up immediately
      8. Mark session as reflection_done = true

    Returns the reflection dict on success, empty dict on failure.
    """
    # Check if reflection already done for this session
    session = db.get_session(session_id, user_id)
    if session and session.get("reflection_done"):
        logger.info(f"Reflection already done for session {session_id}, skipping.")
        return {}

    # Load transcript
    messages = db.get_session_messages(session_id, limit=200)
    if len(messages) < MIN_MESSAGES_FOR_REFLECTION:
        logger.info(
            f"Session {session_id} has only {len(messages)} messages — "
            f"skipping reflection (need ≥{MIN_MESSAGES_FOR_REFLECTION})."
        )
        return {}

    transcript = _build_transcript(messages)
    profile_narrative = get_profile_narrative(user_id, db) or "No profile available yet."

    # Run reflection LLM
    llm = get_llm_service()
    reflection_prompt = build_reflection_prompt(profile_narrative, transcript)

    try:
        reflection = llm.complete_json(
            system_prompt=(
                "You are an expert therapist reviewing a completed session. "
                "Extract structured learnings to improve future sessions. "
                "Return only valid JSON."
            ),
            user_message=reflection_prompt,
            temperature=0.3,
        )
    except Exception as e:
        logger.error(f"Reflection LLM call failed for session {session_id}: {e}")
        return {}

    logger.info(f"Reflection completed for session {session_id}.")

    # Store episodic chunks in ChromaDB
    key_moments = reflection.get("key_moments", [])
    if isinstance(key_moments, list):
        chunk_ids = _store_episodic_chunks(user_id, session_id, key_moments)
        reflection["chunk_ids"] = chunk_ids

        # Invalidate BM25 cache so the new chunks are picked up on next retrieval
        if chunk_ids:
            invalidate_cache(user_id)

    # Store mood score in Supabase
    mood_score = reflection.get("mood_score")
    if mood_score is not None:
        try:
            score_val = float(mood_score)
            db.create_mood_entry(user_id, session_id, score_val)
            logger.info(f"Mood score {score_val} stored for session {session_id}")
        except (ValueError, TypeError):
            logger.warning(f"Invalid mood_score value: {mood_score}")

    # Persist full reflection JSON + mark done
    db.update_session(session_id, {
        "reflection_json": reflection,
        "reflection_done": True,
    })

    return reflection


def store_episodic_chunk(
    user_id: str,
    session_id: str,
    content: str,
    importance_flag: bool = False,
    topics: Optional[list[str]] = None,
) -> str:
    """
    Store a single episodic memory chunk manually.
    Returns the chunk_id.
    """
    chunk_id = f"episodic_{user_id}_{session_id}_{uuid.uuid4().hex[:8]}"
    collection = get_episodic_collection(user_id)
    embedder = get_embedder()
    embedding = embedder.embed_document(content)

    metadata = {
        "user_id": user_id,
        "session_id": session_id,
        "type": "episodic_moment",
        "importance_flag": importance_flag,
    }
    if topics:
        metadata["topics"] = ", ".join(topics)

    collection.upsert(
        ids=[chunk_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[metadata],
    )
    invalidate_cache(user_id)
    return chunk_id
