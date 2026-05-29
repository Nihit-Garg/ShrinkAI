"""
Post-session reflection prompt.
Run after every session ends — extracts learnings and updates the episodic memory.
"""

REFLECTION_PROMPT_TEMPLATE = """You have just finished a therapy conversation. Your job is to carefully review what happened and extract what you learned about this person.

## Existing Profile Summary
{profile_narrative}

## This Session's Conversation
{session_transcript}

---

Answer the following questions. Be concise, specific, and grounded in what was actually said — don't infer beyond what the conversation supports.

1. **New learnings**: What genuinely new things did you learn about this person? (Their feelings, patterns, history, relationships, beliefs)

2. **Emotional patterns**: What emotional patterns were visible in this session? (Defensiveness, hope, avoidance, openness, etc.)

3. **Topics avoided**: Did the person sidestep or minimize anything? What did they avoid? Be specific.

4. **Progress moments**: Were there any moments of insight, growth, or positive shift? Quote the person if possible.

5. **Profile updates needed**: Based on this session, what in the existing profile should be added, modified, or noted as potentially outdated?

6. **Key moments to store**: Identify 1–3 specific moments from this session worth storing as episodic memory. For each, write a 1–2 sentence summary.

7. **Session mood score**: Rate the overall emotional tone of this session from -1.0 (very distressed) to 1.0 (very positive/hopeful). Consider both what was said and the emotional arc. Return only the number.

Return your response as valid JSON with these exact keys:
{{
  "new_learnings": "...",
  "emotional_patterns": "...",
  "topics_avoided": "...",
  "progress_moments": "...",
  "profile_updates": "...",
  "key_moments": ["...", "..."],
  "mood_score": 0.0
}}"""


def build_reflection_prompt(profile_narrative: str, session_transcript: str) -> str:
    return REFLECTION_PROMPT_TEMPLATE.format(
        profile_narrative=profile_narrative,
        session_transcript=session_transcript,
    )
