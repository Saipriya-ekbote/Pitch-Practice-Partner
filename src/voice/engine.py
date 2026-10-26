"""
Voice Engine for Pitch Practice Partner (Phase 8).
Coordinates speech-to-text transcription, text-to-speech synthesis,
audio validation, and objective speech delivery metrics.
Follows Dependency Injection principles; strictly NOT a singleton.
"""

import logging
from typing import Optional, Tuple, Any

from src.voice.voice_models import AudioData, STTResult, TTSResult, SpeechMetrics
from src.voice.provider import STTProvider, TTSProvider
from src.voice.metrics import calculate_speech_metrics
from src.voice.audio_utils import validate_audio_data

logger = logging.getLogger(__name__)


def get_voice_service(
    stt_provider: Optional[STTProvider] = None,
    tts_provider: Optional[TTSProvider] = None,
) -> "VoiceEngine":
    """
    Factory helper to obtain a new VoiceEngine instance with demo defaults.
    Ensures a fresh instance is constructed each time (NOT a singleton).

    Args:
        stt_provider: Optional STT provider; defaults to DemoSTTProvider.
        tts_provider: Optional TTS provider; defaults to DemoTTSProvider.

    Returns:
        Configured VoiceEngine instance.
    """
    from src.voice.stt.demo_stt import DemoSTTProvider
    from src.voice.tts.demo_tts import DemoTTSProvider

    stt = stt_provider or DemoSTTProvider()
    tts = tts_provider or DemoTTSProvider()
    return VoiceEngine(stt_provider=stt, tts_provider=tts)


class VoiceEngine:
    """
    Voice interaction engine coordinating STT, TTS, and Speech Intelligence.
    Uses Dependency Injection for providers to allow swappable demo and real integrations.
    Instantiated per session or controller; strictly NOT a singleton.

    VoiceEngine responsibilities ONLY:
    1. Validate audio
    2. Call STT provider
    3. Return transcription
    4. Calculate speech metrics
    5. Call TTS provider
    6. Return synthesized audio
    """

    def __init__(
        self,
        stt_provider: STTProvider,
        tts_provider: TTSProvider,
    ) -> None:
        """
        Initialize VoiceEngine with injected STT and TTS providers.

        Args:
            stt_provider: Concrete implementation of STTProvider.
            tts_provider: Concrete implementation of TTSProvider.
        """
        if stt_provider is None:
            raise ValueError("VoiceEngine requires a non-None 'stt_provider'.")
        if tts_provider is None:
            raise ValueError("VoiceEngine requires a non-None 'tts_provider'.")

        self.stt_provider = stt_provider
        self.tts_provider = tts_provider

    def validate_audio(
        self,
        raw_bytes: bytes,
        audio_format: str = "wav",
        duration_seconds: Optional[float] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate audio integrity, format, size limits, and duration boundaries.

        Args:
            raw_bytes: Audio byte content.
            audio_format: Container format identifier.
            duration_seconds: Optional recorded duration in seconds.

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str]).
        """
        return validate_audio_data(
            raw_bytes=raw_bytes,
            audio_format=audio_format,
            duration_seconds=duration_seconds,
        )

    def process_speech_input(
        self,
        audio: Any,
        audio_format: str = "wav",
        duration_seconds: Optional[float] = None,
    ) -> Tuple[STTResult, SpeechMetrics]:
        """
        Validate input audio, transcribe via STT provider, and calculate objective speech metrics.

        Args:
            audio: AudioData instance or raw audio bytes.
            audio_format: Container format if audio is passed as raw bytes.
            duration_seconds: Measured recording duration if audio is passed as raw bytes.

        Returns:
            Tuple of (STTResult, SpeechMetrics).

        Raises:
            ValueError: If input audio fails validation.
        """
        if isinstance(audio, (bytes, bytearray)):
            audio_obj = AudioData(
                raw_bytes=bytes(audio),
                audio_format=audio_format,
                duration_seconds=duration_seconds,
            )
        elif isinstance(audio, AudioData):
            audio_obj = audio
        else:
            raise TypeError("Expected AudioData or bytes for audio input.")

        is_valid, err_msg = self.validate_audio(
            raw_bytes=audio_obj.raw_bytes,
            audio_format=audio_obj.audio_format,
            duration_seconds=audio_obj.duration_seconds,
        )
        if not is_valid:
            raise ValueError(f"Audio validation failed: {err_msg}")

        # 1. Transcribe audio
        try:
            stt_result = self.stt_provider.transcribe(audio_obj)
        except Exception as e:
            logger.error("STT provider transcription failed: %s", e)
            stt_result = STTResult(
                text="",
                confidence=None,
                duration_seconds=audio_obj.duration_seconds,
                is_simulated=getattr(self.stt_provider, "is_demo", False),
                error=f"Transcription failed: {str(e)}",
            )

        # 2. Compute speech delivery metrics
        effective_duration = (
            audio_obj.duration_seconds if audio_obj.duration_seconds is not None and audio_obj.duration_seconds > 0.0
            else stt_result.duration_seconds
        )
        metrics = calculate_speech_metrics(
            transcript=stt_result.text,
            recording_duration_seconds=effective_duration,
            confidence=stt_result.confidence,
            is_simulated=stt_result.is_simulated,
        )

        return stt_result, metrics

    def transcribe(self, audio: AudioData) -> Tuple[STTResult, SpeechMetrics]:
        """Alias for process_speech_input for convenient AudioData handling."""
        return self.process_speech_input(audio=audio)

    def synthesize(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        """
        Synthesize AI persona text response into speech audio bytes.
        Handles provider exceptions gracefully so failures do not crash the application.

        Args:
            text: Text response to synthesize.
            voice_id: Optional voice archetype identifier.

        Returns:
            TTSResult with playable audio bytes or error status.
        """
        try:
            return self.tts_provider.synthesize(text, voice_id=voice_id)
        except Exception as e:
            logger.error("TTS provider synthesis failed: %s", e)
            return TTSResult(
                audio_bytes=b"",
                audio_format="audio/wav",
                duration_seconds=None,
                error=f"Synthesis failed: {str(e)}",
            )

    def synthesize_response(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        """Alias for synthesize."""
        return self.synthesize(text, voice_id=voice_id)
