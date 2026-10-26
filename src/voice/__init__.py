"""
Voice Interaction & Speech Intelligence Package (Phase 8).
"""

from src.voice.voice_models import (
    AudioData,
    STTResult,
    TTSResult,
    SpeechMetrics,
)
from src.voice.provider import (
    STTProvider,
    TTSProvider,
)
from src.voice.stt.demo_stt import DemoSTTProvider
from src.voice.tts.demo_tts import DemoTTSProvider
from src.voice.metrics import calculate_speech_metrics
from src.voice.engine import VoiceEngine
from src.voice.audio_utils import extract_wav_duration, validate_audio_data

VoiceService = VoiceEngine


def get_voice_service(stt_provider: STTProvider = None, tts_provider: TTSProvider = None) -> VoiceEngine:
    """Factory helper to obtain a VoiceEngine / VoiceService instance with demo defaults."""
    stt = stt_provider or DemoSTTProvider()
    tts = tts_provider or DemoTTSProvider()
    return VoiceEngine(stt_provider=stt, tts_provider=tts)


__all__ = [
    "AudioData",
    "STTResult",
    "TTSResult",
    "SpeechMetrics",
    "STTProvider",
    "TTSProvider",
    "DemoSTTProvider",
    "DemoTTSProvider",
    "calculate_speech_metrics",
    "VoiceEngine",
    "VoiceService",
    "get_voice_service",
    "extract_wav_duration",
    "validate_audio_data",
]

