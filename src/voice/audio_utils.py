"""
Audio utilities for Pitch Practice Partner (Phase 8).
Provides WAV header inspection, duration extraction, and format validation
using only standard Python libraries (wave, struct, io).
"""

import io
import wave
from typing import Optional, Tuple

SUPPORTED_AUDIO_FORMATS = {
    "wav",
    "webm",
    "mp3",
    "ogg",
    "m4a",
    "audio/wav",
    "audio/webm",
    "audio/mp3",
    "audio/ogg",
    "audio/x-wav",
}
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25 Megabytes
MIN_AUDIO_DURATION_SEC = 0.2
MAX_AUDIO_DURATION_SEC = 300.0  # 5 minutes


def extract_wav_duration(audio_bytes: bytes) -> Optional[float]:
    """
    Extract exact recording duration in seconds from WAV header.
    Returns None if audio_bytes is not a valid WAV file.
    """
    if not audio_bytes or len(audio_bytes) < 44:
        return None
    try:
        buffer = io.BytesIO(audio_bytes)
        with wave.open(buffer, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return round(float(frames) / float(rate), 3)
    except Exception:
        pass
    return None


def validate_audio_data(
    raw_bytes: bytes,
    audio_format: str = "wav",
    duration_seconds: Optional[float] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate audio byte integrity, container format, size limits, and duration boundaries.
    
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str]).
    """
    if not raw_bytes or len(raw_bytes) == 0:
        return False, "Audio recording is empty (0 bytes received)."

    if len(raw_bytes) > MAX_AUDIO_SIZE_BYTES:
        max_mb = MAX_AUDIO_SIZE_BYTES / (1024 * 1024)
        return False, f"Audio file exceeds maximum size limit of {max_mb:.1f} MB."

    clean_format = audio_format.lower().strip()
    if clean_format not in SUPPORTED_AUDIO_FORMATS:
        return False, f"Unsupported audio format '{audio_format}'. Supported formats: {sorted(list(SUPPORTED_AUDIO_FORMATS))}."

    # If duration is provided or can be extracted from WAV
    dur = duration_seconds
    if (dur is None or dur <= 0.0) and ("wav" in clean_format):
        dur = extract_wav_duration(raw_bytes)

    if dur is not None:
        if dur < MIN_AUDIO_DURATION_SEC:
            return False, f"Audio duration ({dur:.2f}s) is too short. Minimum required is {MIN_AUDIO_DURATION_SEC}s."
        if dur > MAX_AUDIO_DURATION_SEC:
            return False, f"Audio duration ({dur:.1f}s) exceeds maximum allowed {MAX_AUDIO_DURATION_SEC}s."

    return True, None
