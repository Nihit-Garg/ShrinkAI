from pydantic import BaseModel
from typing import Literal
import uuid


class MessageRequest(BaseModel):
    content: str
    session_id: str | None = None  # If None, a new session is created


class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    content: str
    role: Literal["assistant"]
    crisis_detected: bool = False


class SessionResponse(BaseModel):
    session_id: str
    started_at: str
    message_count: int


class ConversationHistoryResponse(BaseModel):
    session_id: str
    messages: list[dict]
