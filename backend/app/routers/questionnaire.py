from fastapi import APIRouter, Depends, HTTPException, status
from app.db_client import SupabaseDB, get_db
from app.middleware.auth import get_current_user
from app.schemas.questionnaire import (
    QuestionnaireSubmitRequest,
    QuestionnaireStatusResponse,
    QuestionsListResponse,
    QuestionDefinition,
)
from app.services.questionnaire_service import (
    process_questionnaire,
    has_completed_questionnaire,
)
from app.questionnaire_definitions import QUESTIONS, FRAMING_STATEMENT
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/questionnaire", tags=["Questionnaire"])


@router.get("/questions", response_model=QuestionsListResponse)
async def get_questions():
    """
    Returns the canonical list of onboarding questions.
    Frontend calls this to render the questionnaire — single source of truth.
    No auth required (questions are not user-specific).
    """
    return QuestionsListResponse(
        framing_statement=FRAMING_STATEMENT,
        questions=[
            QuestionDefinition(id=q["id"], text=q["text"])
            for q in QUESTIONS
        ],
    )


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_questionnaire(
    body: QuestionnaireSubmitRequest,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
):
    """
    Submit onboarding questionnaire answers.

    Accepts partial responses — null values mean the question was skipped.
    Skipped questions are stored and treated as data (avoidance is informative).

    Pipeline triggered:
      answers → LLM narrative (Pass 1) → LLM structured extraction (Pass 2)
      → nomic-embed-text embedding → ChromaDB + Supabase storage
    """
    user_id = current_user["user_id"]

    if not body.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questionnaire answers cannot be empty.",
        )

    answered_count = sum(
        1 for v in body.answers.values()
        if v is not None and str(v).strip()
    )
    if answered_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one question must be answered.",
        )

    try:
        profile = process_questionnaire(
            user_id=user_id,
            answers=body.answers,
            db=db,
        )
        return {
            "message": "Questionnaire processed successfully.",
            "user_id": profile.get("user_id") if isinstance(profile, dict) else user_id,
            "reassess_due": profile.get("reassess_due") if isinstance(profile, dict) else None,
            "answered": answered_count,
            "skipped": len(body.answers) - answered_count,
        }
    except Exception as e:
        logger.error(f"Questionnaire processing failed for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process questionnaire. Please try again.",
        )


@router.get("/status", response_model=QuestionnaireStatusResponse)
async def questionnaire_status(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
):
    """Check whether the current user has completed their onboarding questionnaire."""
    user_id = current_user["user_id"]
    completed = has_completed_questionnaire(user_id, db)

    if not completed:
        return QuestionnaireStatusResponse(completed=False)

    profile = db.get_user_profile(user_id)
    return QuestionnaireStatusResponse(
        completed=True,
        reassess_due=profile.get("reassess_due") if profile else None,
    )
