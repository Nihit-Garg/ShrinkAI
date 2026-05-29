"""
Canonical questionnaire definition.

Single source of truth for question IDs, text, and psychological intent.
Frontend fetches this via GET /questionnaire/questions.
Backend uses the intent metadata to guide the LLM extraction pass.
"""

FRAMING_STATEMENT = (
    "There are no right or wrong answers here. This isn't a test. "
    "The more honest you are, the better I'll understand you — and the more useful I can actually be. "
    "Take your time."
)

QUESTIONS = [
    {
        "id": "q01_entry_point",
        "text": "What made you open this today — not the general reason, the specific thing that happened or the feeling you woke up with?",
        "intent": "Immediate presenting state; entry point into their world.",
        "extracts": "emotional_baseline",
    },
    {
        "id": "q02_coping_style",
        "text": "When something is really bothering you, what do you usually do with it?",
        "intent": "Coping style, avoidance patterns, emotional processing type.",
        "extracts": "coping_style",
    },
    {
        "id": "q03_proud_self",
        "text": "Describe a version of yourself you were proud of — when was that, and what was different about your life then?",
        "intent": "Self-concept, what they value, what they feel they've lost or moved away from.",
        "extracts": "key_relationships",
    },
    {
        "id": "q04_social_support",
        "text": "Who in your life right now actually gets you — and if no one, when did that last feel true?",
        "intent": "Social support map, loneliness indicators, attachment style signals.",
        "extracts": "key_relationships",
    },
    {
        "id": "q05_intrusive_thought",
        "text": "What's the thought you have most often that you wish you could turn off?",
        "intent": "Core cognitive distortions, rumination patterns, inner critic voice.",
        "extracts": "core_fear",
    },
    {
        "id": "q06_misunderstood",
        "text": "What do people in your life consistently get wrong about you?",
        "intent": "Gap between self-perception and perceived external image, unmet need to be understood.",
        "extracts": "emotional_baseline",
    },
    {
        "id": "q07_future_desire",
        "text": "When you imagine your life a year from now and it's genuinely better — what's the one thing that changed?",
        "intent": "Core desire, what they're actually working toward, where the pain is concentrated.",
        "extracts": "presenting_goal",
    },
    {
        "id": "q08_unsaid_thing",
        "text": "Is there something you've never said out loud to anyone that you think about often?",
        "intent": "Shame material, suppressed narrative, depth of trust — even a skip is data.",
        "extracts": "core_fear",
    },
    {
        "id": "q09_self_treatment_on_failure",
        "text": "How do you treat yourself when you fail at something — be honest, not how you think you should?",
        "intent": "Self-compassion level, inner critic intensity, impossible standards.",
        "extracts": "coping_style",
    },
    {
        "id": "q10_body_on_bad_day",
        "text": "What does a bad day feel like in your body — not emotionally, physically?",
        "intent": "Somatic awareness, how embodied their emotional experience is, stress response type.",
        "extracts": "emotional_baseline",
    },
    {
        "id": "q11_self_concept_origin",
        "text": "Who or what shaped the way you see yourself most — and is that a good thing?",
        "intent": "Origin of self-concept, family dynamics, formative relationships or events.",
        "extracts": "key_relationships",
    },
    {
        "id": "q12_core_shame",
        "text": "What are you most afraid people would think if they could see everything — your thoughts, your choices, your life as it actually is?",
        "intent": "Core shame, what they're hiding, the gap between public self and private self.",
        "extracts": "core_fear",
    },
    {
        "id": "q13_open_close",
        "text": "Is there anything you want me to know about you that none of those questions touched?",
        "intent": "Volunteer unprompted data — most important. What they choose to add reveals what they feel matters most.",
        "extracts": "presenting_goal",
    },
]

# Flat dict for O(1) lookup by ID
QUESTIONS_BY_ID: dict[str, dict] = {q["id"]: q for q in QUESTIONS}


def get_question_ids() -> list[str]:
    return [q["id"] for q in QUESTIONS]


def build_intent_context() -> str:
    """
    Generates a rich string describing each question's psychological intent.
    Injected into the LLM extraction prompt so it understands WHY each question was asked.
    """
    lines = []
    for q in QUESTIONS:
        lines.append(f"- {q['id']}: \"{q['text']}\"\n  Intent: {q['intent']}")
    return "\n".join(lines)
