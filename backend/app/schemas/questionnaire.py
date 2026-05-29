from pydantic import BaseModel, field_validator
from typing import Optional


class QuestionnaireSubmitRequest(BaseModel):
    """
    Answers to the onboarding questionnaire.

    `answers` maps question_id → answer text OR None (explicitly skipped).
    Skipped questions must still be included as None — this is intentional:
    a skipped q08_unsaid_thing tells us as much as an answer does.

    Example:
        {
            "q01_entry_point": "I woke up anxious and couldn't shake it.",
            "q08_unsaid_thing": null,   ← skipped
            ...
        }
    """
    answers: dict[str, Optional[str]]

    @field_validator("answers")
    @classmethod
    def must_have_at_least_one_answer(cls, v: dict) -> dict:
        answered = [val for val in v.values() if val is not None and val.strip()]
        if not answered:
            raise ValueError("At least one question must be answered.")
        return v


class QuestionnaireStatusResponse(BaseModel):
    completed: bool
    reassess_due: Optional[str] = None  # ISO datetime string


class QuestionDefinition(BaseModel):
    """Returned by GET /questionnaire/questions."""
    id: str
    text: str


class QuestionsListResponse(BaseModel):
    framing_statement: str
    questions: list[QuestionDefinition]
