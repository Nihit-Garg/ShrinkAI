"""
Questionnaire Service — updated to use the canonical question definitions
and two-pass LLM processing:

Pass 1 — Narrative: warm, third-person psychological profile for the therapist
Pass 2 — Structured Extraction: 5 JSON dimensions for queryable profile data

Both outputs are stored in Supabase user_profiles:
  - questionnaire: the raw answers dict (with nulls for skips)
  - narrative: the warm prose profile (injected into every system prompt)
  - structured_profile: the 5 extracted dimensions (for future intent-routing)
"""
import json
import logging
from typing import Optional

from app.db_client import SupabaseDB
from app.services.llm_service import get_llm_service
from app.vector_store import get_profile_collection, get_embedder
from app.questionnaire_definitions import (
    QUESTIONS,
    QUESTIONS_BY_ID,
    FRAMING_STATEMENT,
    build_intent_context,
)

logger = logging.getLogger(__name__)


# ── LLM Prompts ───────────────────────────────────────────────────────────────

_NARRATIVE_SYSTEM = """You are creating a rich psychological profile for a therapist who is about to meet this person for the first time.

Based on the questionnaire responses below, write a warm, insightful, third-person profile in 3–4 paragraphs.

Guidelines:
- Write as if briefing a skilled, empathetic therapist before session one
- Use their EXACT words and phrases where they reveal something — their language matters
- Treat skipped questions as data: note the avoidance without judgment ("They chose not to answer what they think about often — this may be worth approaching gently over time")
- Cover: emotional landscape and presenting state, coping style and patterns, how they see themselves vs how they think others see them, core desires and fears, relationships and support, what kind of support they seem to need
- Be specific, not generic — every profile should feel unmistakably written for this specific person
- Do NOT use clinical diagnoses or labels
- Do NOT give advice — this is an observation document, not a treatment plan"""

_NARRATIVE_USER_TEMPLATE = """Here are the questionnaire questions and their psychological intent:

{intent_context}

---

Here are this person's responses (null = question was skipped):

{formatted_answers}

---

Write the profile narrative now."""


_EXTRACTION_SYSTEM = """You are a clinical psychologist extracting structured psychological dimensions from a completed intake questionnaire.

Extract EXACTLY these 5 dimensions as a JSON object. Be specific — use the person's own words and concrete details, not generic summaries.

Required JSON structure:
{{
  "emotional_baseline": "1-2 sentences describing their current emotional state and how they typically experience difficult emotions",
  "coping_style": "1-2 sentences on how they process and respond to stress, difficulty, or pain — including avoidant patterns",
  "core_fear": "1-2 sentences on what they are most afraid of — about themselves, their life, how others see them",
  "key_relationships": "1-2 sentences on their support system, attachment style signals, loneliness, key figures",
  "presenting_goal": "1-2 sentences on what they actually want from this — the underlying need, not the surface request"
}}

If a question was skipped, use what IS available from other answers to infer the dimension. If truly unknowable, write "Insufficient data — worth exploring gently."

Return ONLY the JSON object. No markdown, no explanation."""

_EXTRACTION_USER_TEMPLATE = """Questions with psychological intent:

{intent_context}

---

Responses (null = skipped):

{formatted_answers}

---

Extract the 5 dimensions now."""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _format_answers(answers: dict[str, Optional[str]]) -> str:
    """Format answers for LLM consumption, clearly marking skips."""
    lines = []
    for q in QUESTIONS:
        qid = q["id"]
        answer = answers.get(qid)
        q_text = q["text"]
        if answer is None or not answer.strip():
            lines.append(f"Q ({qid}): {q_text}\nA: [skipped]")
        else:
            lines.append(f"Q ({qid}): {q_text}\nA: {answer.strip()}")
    return "\n\n".join(lines)


# ── Pass 1: Narrative generation ───────────────────────────────────────────────

def generate_narrative(answers: dict[str, Optional[str]]) -> str:
    """Generate a warm, third-person psychological profile narrative."""
    llm = get_llm_service()
    formatted = _format_answers(answers)
    intent_ctx = build_intent_context()

    narrative = llm.complete(
        system_prompt=_NARRATIVE_SYSTEM,
        user_message=_NARRATIVE_USER_TEMPLATE.format(
            intent_context=intent_ctx,
            formatted_answers=formatted,
        ),
        temperature=0.65,
        max_tokens=1000,
    )
    logger.info("Profile narrative generated successfully.")
    return narrative


# ── Pass 2: Structured extraction ──────────────────────────────────────────────

_FALLBACK_STRUCTURED = {
    "emotional_baseline": "Insufficient data.",
    "coping_style": "Insufficient data.",
    "core_fear": "Insufficient data.",
    "key_relationships": "Insufficient data.",
    "presenting_goal": "Insufficient data.",
}

def extract_structured_profile(answers: dict[str, Optional[str]]) -> dict:
    """
    Extract 5 structured psychological dimensions as JSON.
    Falls back gracefully if parsing fails.
    """
    llm = get_llm_service()
    formatted = _format_answers(answers)
    intent_ctx = build_intent_context()

    try:
        result = llm.complete_json(
            system_prompt=_EXTRACTION_SYSTEM,
            user_message=_EXTRACTION_USER_TEMPLATE.format(
                intent_context=intent_ctx,
                formatted_answers=formatted,
            ),
            temperature=0.3,
        )
        # Validate all 5 keys are present
        required = {"emotional_baseline", "coping_style", "core_fear", "key_relationships", "presenting_goal"}
        if not required.issubset(result.keys()):
            logger.warning("Structured extraction missing keys — using partial result.")
            return {**_FALLBACK_STRUCTURED, **result}
        logger.info("Structured profile extracted successfully.")
        return result
    except Exception as e:
        logger.error(f"Structured extraction failed: {e}. Using fallback.")
        return _FALLBACK_STRUCTURED


# ── ChromaDB embed + store ─────────────────────────────────────────────────────

def embed_and_store_profile(
    user_id: str,
    answers: dict[str, Optional[str]],
    narrative: str,
    structured_profile: dict,
    db: SupabaseDB,
) -> dict:
    """
    Embed narrative into ChromaDB and persist everything to Supabase.
    Stores:
      - questionnaire (raw answers with skip nulls)
      - narrative (prose profile)
      - structured_profile (5 extracted JSON dimensions)
      - embedding_id (ChromaDB doc ID)
      - reassess_due (now + 30 days)
    """
    embedder = get_embedder()
    collection = get_profile_collection()

    # Embed the narrative (richer signal than structured JSON for semantic search)
    embedding = embedder.embed_document(narrative)
    embedding_id = f"profile_{user_id}"

    collection.upsert(
        ids=[embedding_id],
        embeddings=[embedding],
        documents=[narrative],
        metadatas=[{
            "user_id": user_id,
            "type": "identity_profile",
            "presenting_goal": structured_profile.get("presenting_goal", ""),
            "core_fear": structured_profile.get("core_fear", ""),
        }],
    )
    logger.info(f"Profile embedding stored in ChromaDB: {embedding_id}")

    from datetime import datetime, timedelta, timezone
    reassess_due = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # Count skipped questions for metadata
    skipped = [qid for qid, ans in answers.items() if ans is None or not str(ans).strip()]

    profile_data = {
        "user_id": user_id,
        "questionnaire": {
            "answers": answers,
            "skipped_question_ids": skipped,
            "total_answered": len(QUESTIONS) - len(skipped),
        },
        "narrative": narrative,
        "structured_profile": structured_profile,
        "embedding_id": embedding_id,
        "reassess_due": reassess_due,
    }
    stored = db.upsert_user_profile(profile_data)
    logger.info(f"Profile stored in Supabase for user: {user_id}")
    return stored


# ── Main pipeline ──────────────────────────────────────────────────────────────

def process_questionnaire(
    user_id: str,
    answers: dict[str, Optional[str]],
    db: SupabaseDB,
) -> dict:
    """
    Full two-pass questionnaire pipeline:
      answers → narrative → structured extraction → embed → store
    Returns the stored profile dict.
    """
    logger.info(f"Processing questionnaire for user {user_id} "
                f"({sum(1 for v in answers.values() if v)} answers, "
                f"{sum(1 for v in answers.values() if not v)} skips)")

    narrative = generate_narrative(answers)
    structured_profile = extract_structured_profile(answers)
    profile = embed_and_store_profile(user_id, answers, narrative, structured_profile, db)
    return profile


# ── Query helpers ──────────────────────────────────────────────────────────────

def get_profile_narrative(user_id: str, db: SupabaseDB) -> Optional[str]:
    """Retrieve the stored narrative for a user."""
    profile = db.get_user_profile(user_id)
    return profile.get("narrative") if profile else None


def get_structured_profile(user_id: str, db: SupabaseDB) -> Optional[dict]:
    """Retrieve the 5 structured dimensions for a user."""
    profile = db.get_user_profile(user_id)
    return profile.get("structured_profile") if profile else None


def has_completed_questionnaire(user_id: str, db: SupabaseDB) -> bool:
    return db.has_completed_questionnaire(user_id)
