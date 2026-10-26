"""
Speech Metrics and Delivery Measurement for Pitch Practice Partner (Phase 8).
Computes factual, observable speech indicators (duration, word count, WPM, fillers).
Reuses the authoritative Phase 4 Conversation Intelligence detector for vocal filler words.
STRICTLY avoids inferring emotion, personality, nervousness, confidence, or honesty.
"""

from typing import Optional, Dict

from src.voice.voice_models import SpeechMetrics
from src.intelligence.detectors import detect_filler_words


def calculate_speech_metrics(
    transcript: str,
    recording_duration_seconds: Optional[float] = None,
    confidence: Optional[float] = None,
    is_simulated: bool = False,
) -> SpeechMetrics:
    """
    Calculate objective, verifiable speech delivery metrics from transcript and recording duration.

    IMPORTANT RULES:
    1. Words Per Minute (WPM) is calculated strictly using actual recording duration:
       word_count / (recording_duration_seconds / 60)
       If reliable recording duration is unavailable (None or < 1.0s):
       words_per_minute = None. Do not estimate.
    2. Filler analysis reuses the existing Phase 4 Conversation Intelligence system (detect_filler_words).
    3. Factual measurements only; strictly no psychological or emotional inferences.

    Args:
        transcript: Transcribed speech text.
        recording_duration_seconds: Measured audio recording duration in seconds (if available).
        confidence: Transcription confidence score between 0.0 and 1.0 (if provided by STT).
        is_simulated: Flag indicating whether metrics derive from demo/simulated audio.

    Returns:
        SpeechMetrics dataclass populated with factual metrics.
    """
    clean_text = transcript.strip() if transcript else ""
    words = clean_text.split() if clean_text else []
    word_count = len(words)

    # WPM requires reliable positive duration (>= 1.0s)
    if recording_duration_seconds is not None and recording_duration_seconds >= 1.0 and word_count > 0:
        minutes = recording_duration_seconds / 60.0
        wpm = round(word_count / minutes, 1)
    else:
        wpm = None

    # Reuse Phase 4 authoritative filler word detector
    filler_counts: Dict[str, int] = detect_filler_words(clean_text) if clean_text else {}
    total_fillers = sum(filler_counts.values())
    filler_pct = round((total_fillers / word_count * 100.0), 1) if word_count > 0 else 0.0

    return SpeechMetrics(
        recording_duration_seconds=recording_duration_seconds,
        word_count=word_count,
        words_per_minute=wpm,
        confidence=confidence,
        filler_count=total_fillers,
        filler_percentage=filler_pct,
        is_simulated=is_simulated,
    )
