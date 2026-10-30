import re
from typing import List, Tuple
from app.schemas.models import SpeechMetrics

FILLER_PATTERNS = [
    r"\bum\b",
    r"\buh\b",
    r"\ber\b",
    r"\bah\b",
    r"\blike\b",
    r"\byou know\b",
    r"\bbasically\b",
    r"\bactually\b",
    r"\bliterally\b",
    r"\bsort of\b",
    r"\bkind of\b",
    r"\bi mean\b",
]

def analyze_speech_delivery(transcript: str) -> SpeechMetrics:
    """
    Analyzes candidate spoken transcript for delivery cadence, filler words, and clarity.
    """
    if not transcript or not transcript.strip():
        return SpeechMetrics(
            wpm=0,
            filler_word_count=0,
            filler_words_detected=[],
            pacing_rating="No Speech Detected",
            clarity_score=0
        )

    words = re.findall(r"\b\w+\b", transcript.lower())
    total_words = len(words)

    detected_fillers: List[str] = []
    text_lower = transcript.lower()
    for pattern in FILLER_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            detected_fillers.extend(matches)

    filler_count = len(detected_fillers)

    # Estimate WPM: an average conversational candidate answer is spoken in 30-45 seconds
    # If transcript has N words, estimate realistic conversational pace
    # In live speech recognition, word rate per 40-sec block:
    estimated_minutes = max(0.5, total_words / 130.0)
    wpm = int(total_words / estimated_minutes)

    if wpm < 110:
        pacing = "Hesitant / Slow"
    elif 110 <= wpm <= 165:
        pacing = "Optimal Cadence"
    else:
        pacing = "Fast / Rushed"

    # Clarity rating (1 to 10)
    # Deduct points if filler ratio > 5% of words
    filler_ratio = filler_count / max(1, total_words)
    deduction = min(5, int(filler_ratio * 30))
    clarity = max(3, min(10, 10 - deduction))

    return SpeechMetrics(
        wpm=wpm,
        filler_word_count=filler_count,
        filler_words_detected=list(set(detected_fillers)),
        pacing_rating=pacing,
        clarity_score=clarity
    )
