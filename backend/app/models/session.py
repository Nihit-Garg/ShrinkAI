"""SQLAlchemy ORM model for sessions table."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.user_id"), nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)
    mood_score = Column(Float, nullable=True, comment="Sentiment score -1.0 to 1.0")
    crisis_flag = Column(Boolean, default=False)
    reflection_done = Column(Boolean, default=False)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    mood_entry = relationship("MoodEntry", back_populates="session", uselist=False)
