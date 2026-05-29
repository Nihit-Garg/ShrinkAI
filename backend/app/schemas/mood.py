from pydantic import BaseModel


class MoodEntryResponse(BaseModel):
    session_id: str
    score: float
    recorded_at: str


class MoodTrendResponse(BaseModel):
    entries: list[MoodEntryResponse]
    average_score: float | None
