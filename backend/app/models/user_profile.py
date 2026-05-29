"""
SQLAlchemy ORM model for user_profiles table.
Stores the questionnaire answers, LLM-generated narrative, and ChromaDB embedding reference.
"""
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="FK to Supabase auth.users — same UUID",
    )
    questionnaire = Column(
        JSON,
        nullable=False,
        comment="Raw questionnaire answers as submitted by the user",
    )
    narrative = Column(
        Text,
        nullable=True,
        comment="LLM-generated psychological profile narrative (2-3 paragraphs)",
    )
    embedding_id = Column(
        String(255),
        nullable=True,
        comment="ChromaDB document ID for the embedded narrative",
    )
    reassess_due = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the questionnaire should be re-evaluated (created_at + 30 days)",
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @classmethod
    def make_reassess_due(cls) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=30)
