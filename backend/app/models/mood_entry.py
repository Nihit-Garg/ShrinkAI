"""SQLAlchemy ORM model for mood_entries table."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class MoodEntry(Base):
    __tablename__ = "mood_entries"

    entry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.user_id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id"), nullable=False)
    score = Column(Float, nullable=False, comment="Sentiment score -1.0 (very negative) to 1.0 (very positive)")
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("Session", back_populates="mood_entry")
