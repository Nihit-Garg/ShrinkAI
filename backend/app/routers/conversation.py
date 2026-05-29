"""
Conversation router — Week 3+4 update.

Changes from Week 1:
- user_message passed to assemble_context() for query-aware episodic retrieval
- BackgroundTasks used to trigger post-session reflection after 5th assistant message
- end-session endpoint now fully wired to run reflection pipeline
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from app.db_client import SupabaseDB, get_db
from app.middleware.auth import get_current_user
from app.schemas.conversation import MessageRequest, MessageResponse, ConversationHistoryResponse
from app.services.llm_service import get_llm_service
from app.services.context_assembler import assemble_context
from app.services.crisis_service import detect_crisis
from app.services.questionnaire_service import has_completed_questionnaire
from app.services.memory_service import run_post_session_reflection
from app.prompts.system_prompt import build_system_prompt
from app.prompts.crisis_prompt import build_crisis_response_prompt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversation", tags=["Conversation"])

# Trigger reflection after every N assistant messages within a session
REFLECTION_TRIGGER_EVERY_N = 5


def _count_assistant_messages(messages: list[dict]) -> int:
    return sum(1 for m in messages if m.get("role") == "assistant")


def _maybe_trigger_reflection(
    user_id: str,
    session_id: str,
    db: SupabaseDB,
) -> None:
    """
    Background task: run reflection if we've hit a trigger point
    and reflection hasn't been done yet for this session.

    This runs in the background after every message response is sent,
    so it never blocks the user waiting for a reply.
    """
    session = db.get_session(session_id, user_id)
    if not session or session.get("reflection_done"):
        return

    messages = db.get_session_messages(session_id, limit=200)
    n_assistant = _count_assistant_messages(messages)

    # Trigger at 5, 10, 15... messages (progressive reflection)
    if n_assistant > 0 and n_assistant % REFLECTION_TRIGGER_EVERY_N == 0:
        logger.info(
            f"Auto-triggering reflection for session {session_id} "
            f"at {n_assistant} assistant messages."
        )
        run_post_session_reflection(user_id, session_id, db)


@router.post("/message", response_model=MessageResponse)
async def send_message(
    body: MessageRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
):
    """
    Send a message and receive an AI therapist response.
    Requires completed questionnaire — returns 403 if not done.

    After every 5th assistant message, a post-session reflection runs
    in the background to extract and store episodic memories.
    """
    user_id = current_user["user_id"]

    # Guard: questionnaire must be completed
    if not has_completed_questionnaire(user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please complete your onboarding questionnaire before starting a conversation.",
        )

    # Get or create session
    if body.session_id:
        session = db.get_session(body.session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")
    else:
        session = db.create_session(user_id)

    session_id = session["session_id"]

    # ── Crisis detection ───────────────────────────────────────────────────────
    is_crisis, crisis_category = detect_crisis(body.content)

    if is_crisis:
        logger.warning(f"Crisis detected ({crisis_category}) for user {user_id}")
        db.flag_session_crisis(session_id)

        system_prompt, user_prompt = build_crisis_response_prompt(body.content)
        llm = get_llm_service()
        ai_response = llm.complete(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.4,
            max_tokens=512,
        )
    else:
        # ── Normal RAG flow ────────────────────────────────────────────────────
        # Pass user message as the retrieval query for episodic context
        context = assemble_context(user_id, session_id, db, user_message=body.content)
        system_prompt = build_system_prompt(**context)

        llm = get_llm_service()
        ai_response = llm.complete(
            system_prompt=system_prompt,
            user_message=body.content,
            temperature=0.75,
            max_tokens=1024,
        )

    # ── Persist both messages ──────────────────────────────────────────────────
    db.create_message(session_id, user_id, "user", body.content)
    ai_msg = db.create_message(session_id, user_id, "assistant", ai_response)

    # ── Background: auto-trigger reflection every 5 assistant messages ─────────
    background_tasks.add_task(
        _maybe_trigger_reflection,
        user_id=user_id,
        session_id=session_id,
        db=db,
    )

    return MessageResponse(
        message_id=ai_msg["message_id"],
        session_id=session_id,
        content=ai_response,
        role="assistant",
        crisis_detected=is_crisis,
    )


@router.post("/end-session")
async def end_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
):
    """
    Explicitly end a conversation session.
    Triggers the full post-session reflection pipeline in the background.
    """
    user_id = current_user["user_id"]
    session = db.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    db.end_session(session_id)

    # Run reflection in background so response is immediate
    background_tasks.add_task(
        run_post_session_reflection,
        user_id=user_id,
        session_id=session_id,
        db=db,
    )

    return {
        "message": "Session ended. Reflection running in background.",
        "session_id": session_id,
    }


@router.get("/history", response_model=ConversationHistoryResponse)
async def get_history(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
):
    """Retrieve all messages for a specific session."""
    user_id = current_user["user_id"]
    session = db.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    messages = db.get_session_messages(session_id, limit=200)
    return ConversationHistoryResponse(
        session_id=session_id,
        messages=[
            {"role": m["role"], "content": m["content"], "created_at": m["created_at"]}
            for m in messages
        ],
    )
