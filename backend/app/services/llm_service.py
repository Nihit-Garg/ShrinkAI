"""
LLM Service — Gemini Flash (primary) + Groq Llama 3.3 70B (fallback).
Uses the new google.genai SDK.

Handles:
- Chat completions (conversation responses)
- Narrative generation (questionnaire → profile text)
- JSON-structured completions (reflection output)
"""
import json
import logging
from typing import Any

from google import genai
from google.genai import types as genai_types
from groq import Groq

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

GEMINI_MODEL = "gemini-2.0-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"


class LLMService:
    """
    Unified LLM interface. All LLM calls in the app go through here.
    Gemini is primary; Groq is the fallback.
    """

    def __init__(self):
        self._gemini = genai.Client(api_key=settings.gemini_api_key)
        self._groq = Groq(api_key=settings.groq_api_key)

    # ── Core completion ────────────────────────────────────────────────────────

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Chat completion with automatic Groq fallback."""
        try:
            return self._gemini_complete(system_prompt, user_message, temperature, max_tokens)
        except Exception as e:
            logger.warning(f"Gemini failed ({type(e).__name__}: {e}). Falling back to Groq.")
            return self._groq_complete(system_prompt, user_message, temperature, max_tokens)

    def complete_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Completion that expects a JSON response. Returns parsed dict."""
        raw = self.complete(
            system_prompt=system_prompt + "\n\nIMPORTANT: Return valid JSON only. No markdown, no code blocks.",
            user_message=user_message,
            temperature=temperature,
            max_tokens=2048,
        )
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)

    # ── Gemini ─────────────────────────────────────────────────────────────────

    def _gemini_complete(
        self, system_prompt: str, user_message: str, temperature: float, max_tokens: int
    ) -> str:
        response = self._gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_message,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text

    # ── Groq (fallback) ────────────────────────────────────────────────────────

    def _groq_complete(
        self, system_prompt: str, user_message: str, temperature: float, max_tokens: int
    ) -> str:
        response = self._groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content


# ── Singleton ──────────────────────────────────────────────────────────────────

_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
