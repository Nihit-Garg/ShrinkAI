"""
Crisis detection service.
Phase 1+2 implementation: keyword + sentiment threshold detection.
Runs in parallel on every incoming user message (non-blocking).

Phase 4 will replace this with a proper parallel pipeline and more sophisticated detection.
"""
import re

# ── Self-harm / suicidal ideation ─────────────────────────────────────────────
# Covers formal English, Gen Z slang, contractions, and common shorthand.
# Deliberately conservative — prefer false positives over misses.

_SELF_HARM_KEYWORDS = [
    # Classic phrasing
    r"\bkill myself\b", r"\bend my life\b", r"\bend it all\b",
    r"\bself.harm\b", r"\bcutting myself\b", r"\bhurt myself\b",
    r"\bwant to die\b", r"\bwish i was dead\b", r"\bbetter off dead\b",
    r"\bsuicid\w*\b",  # suicidal, suicide, suiciding
    r"\bno reason to live\b", r"\bcan't go on\b", r"\bcant go on\b",
    r"\bdon't want to be here\b", r"\bdont want to be here\b",

    # Contractions / colloquial
    r"\bwanna die\b", r"\bi wanna die\b", r"\bwanna end it\b",
    r"\bwant to end it\b", r"\bgonna end it\b", r"\bready to die\b",
    r"\bwanna kms\b", r"\bgonna kms\b",   # "kill myself" shorthand
    r"\bim done with life\b", r"\bi'm done with life\b",
    r"\bno point in living\b", r"\bnot worth living\b",
    r"\blife isn't worth it\b", r"\blife is not worth it\b",
    r"\bi give up on life\b", r"\bgive up on life\b",
    r"\bwanna disappear forever\b", r"\bwant to disappear forever\b",

    # Gen Z / internet slang signals (combined with die/harm context)
    r"\bngl.{0,20}wanna die\b",    # "ngl i wanna die"
    r"\blow.?key.{0,20}wanna die\b",  # "lowkey wanna die"
    r"\bdead.?ass.{0,20}wanna die\b", # "deadass wanna die"
    r"\bfr.{0,10}wanna die\b",    # "fr wanna die"
]

# ── Active danger (harm from others / unsafe environment) ─────────────────────
_ACTIVE_DANGER_KEYWORDS = [
    r"\bsomeone is hurting me\b", r"\bbeing abused\b",
    r"\bi'm not safe\b", r"\bim not safe\b",
    r"\bin danger\b", r"\bscared for my life\b",
    r"\bhe's going to hurt me\b", r"\bshe's going to hurt me\b",
]

# ── Severe distress / acute crisis signals ────────────────────────────────────
_SEVERE_DISTRESS_KEYWORDS = [
    # Breathing / acute physical distress (present tense)
    r"\bcan't breathe\b", r"\bcant breathe\b",
    r"\bhaving a panic attack\b", r"\bi'm panicking\b", r"\bim panicking\b",
    # Dissociation / emotional shutdown
    r"\bdissociat\w*\b", r"\bnumb to everything\b", r"\bfeel nothing\b",
    # Severe isolation
    r"\bcompletely alone\b", r"\bno one cares\b", r"\bnobody cares\b",
    # Rage / violent ideation — emotional escalation signals
    r"\bwanna kill\b", r"\bwant to kill\b", r"\bgoing to kill\b",
    r"\blose control\b", r"\blose it completely\b",
    r"\bi can't control myself\b", r"\bi cant control myself\b",
]
# NOTE: bare "panic attack" removed — too often used descriptively/past-tense.
# NOTE: "kms" alone is NOT included — too many false positives (casual use in gaming etc.)

# NOTE: bare "panic attack" removed — too often used descriptively/past-tense
# ("I had a panic attack last week") which is NOT an active crisis.
# We now require present-tense phrasing: "having a panic attack", "I'm panicking".

_ALL_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in _SELF_HARM_KEYWORDS + _ACTIVE_DANGER_KEYWORDS + _SEVERE_DISTRESS_KEYWORDS
]


def detect_crisis(message: str) -> tuple[bool, str]:
    """
    Returns (is_crisis: bool, category: str).
    Category is one of: 'self_harm', 'active_danger', 'severe_distress', or 'none'.
    """
    msg_lower = message.lower()

    for pattern in [re.compile(p, re.IGNORECASE) for p in _SELF_HARM_KEYWORDS]:
        if pattern.search(message):
            return True, "self_harm"

    for pattern in [re.compile(p, re.IGNORECASE) for p in _ACTIVE_DANGER_KEYWORDS]:
        if pattern.search(message):
            return True, "active_danger"

    for pattern in [re.compile(p, re.IGNORECASE) for p in _SEVERE_DISTRESS_KEYWORDS]:
        if pattern.search(message):
            return True, "severe_distress"

    return False, "none"
