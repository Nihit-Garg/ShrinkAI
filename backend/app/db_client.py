"""
Supabase-based database client.

Replaces SQLAlchemy sessions for all table CRUD operations.
Uses the Supabase REST API (PostgREST) via the supabase-py client,
which authenticates with the service role key — no direct PostgreSQL connection needed.

WHY: The direct PostgreSQL pooler connection (psycopg2) has auth issues on some networks
due to Supabase's IPv6-first infrastructure. The REST API works everywhere.
The service role key bypasses Row Level Security for server-side operations.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from functools import lru_cache

from app.supabase_client import get_supabase_admin


class SupabaseDB:
    """
    Thin wrapper around the Supabase REST client.
    Provides typed methods for each table instead of raw dict access everywhere.
    """

    def __init__(self):
        self.client = get_supabase_admin()

    # ── user_profiles ─────────────────────────────────────────────────────────

    def get_user_profile(self, user_id: str) -> dict | None:
        result = (
            self.client.table("user_profiles")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def upsert_user_profile(self, data: dict) -> dict:
        """Insert or update a user profile. `data` must include `user_id`."""
        result = (
            self.client.table("user_profiles")
            .upsert(data, on_conflict="user_id")
            .execute()
        )
        return result.data[0]

    def has_completed_questionnaire(self, user_id: str) -> bool:
        profile = self.get_user_profile(user_id)
        return profile is not None and profile.get("narrative") is not None

    # ── sessions ──────────────────────────────────────────────────────────────

    def create_session(self, user_id: str) -> dict:
        data = {
            "session_id": str(uuid.uuid4()),
            "user_id": user_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "crisis_flag": False,
            "reflection_done": False,
        }
        result = self.client.table("sessions").insert(data).execute()
        return result.data[0]

    def get_session(self, session_id: str, user_id: str) -> dict | None:
        result = (
            self.client.table("sessions")
            .select("*")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def update_session(self, session_id: str, updates: dict) -> dict:
        result = (
            self.client.table("sessions")
            .update(updates)
            .eq("session_id", session_id)
            .execute()
        )
        return result.data[0]

    def flag_session_crisis(self, session_id: str) -> None:
        self.update_session(session_id, {"crisis_flag": True})

    def end_session(self, session_id: str) -> dict:
        return self.update_session(session_id, {
            "ended_at": datetime.now(timezone.utc).isoformat()
        })

    def get_user_sessions(self, user_id: str, limit: int = 20) -> list[dict]:
        """Return all sessions for a user, newest first."""
        result = (
            self.client.table("sessions")
            .select("*")
            .eq("user_id", user_id)
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    def get_all_session_messages(self, user_id: str, limit_per_session: int = 50) -> list[dict]:
        """Return messages across all sessions for a user (for RAGAS eval)."""
        result = (
            self.client.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .limit(limit_per_session)
            .execute()
        )
        return result.data

    # ── messages ──────────────────────────────────────────────────────────────

    def create_message(
        self, session_id: str, user_id: str, role: str, content: str
    ) -> dict:
        data = {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = self.client.table("messages").insert(data).execute()
        return result.data[0]

    def get_session_messages(
        self, session_id: str, limit: int = 20
    ) -> list[dict]:
        result = (
            self.client.table("messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return result.data

    # ── mood_entries ──────────────────────────────────────────────────────────

    def create_mood_entry(
        self, user_id: str, session_id: str, score: float
    ) -> dict:
        data = {
            "entry_id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_id,
            "score": score,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        result = self.client.table("mood_entries").insert(data).execute()
        return result.data[0]

    def get_mood_trend(self, user_id: str, limit: int = 30) -> list[dict]:
        result = (
            self.client.table("mood_entries")
            .select("score, recorded_at, session_id")
            .eq("user_id", user_id)
            .order("recorded_at", desc=True)
            .limit(limit)
            .execute()
        )
        return list(reversed(result.data))  # Chronological order


def get_db() -> SupabaseDB:
    """
    FastAPI dependency — returns a SupabaseDB instance.
    Replaces the old SQLAlchemy get_db() generator.
    Each request gets a fresh wrapper (the underlying Supabase client is cached).
    """
    return SupabaseDB()
