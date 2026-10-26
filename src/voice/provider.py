"""
Abstract Provider interfaces for Speech-to-Text (STT) and Text-to-Speech (TTS).
Follows the same provider pattern established in src/ai/provider.py.
"""

from abc import ABC, abstractmethod
from typing import Optional

from src.voice.voice_models import AudioData, STTResult, TTSResult


class STTProvider(ABC):
    """
    Abstract interface for Speech-to-Text transcription services.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider descriptive name (e.g. 'Demo STT', 'OpenAI Whisper')."""
        pass

    @property
    @abstractmethod
    def is_demo(self) -> bool:
        """Flag indicating whether this provider runs locally in demo mode."""
        pass

    @abstractmethod
    def transcribe(self, audio: AudioData) -> STTResult:
        """
        Transcribe input speech audio into text.
        
        Args:
            audio: AudioData container with raw bytes, format, sample rate, and duration.
            
        Returns:
            STTResult containing transcribed text, confidence, duration, and simulation flag.
        """
        pass


class TTSProvider(ABC):
    """
    Abstract interface for Text-to-Speech synthesis services.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider descriptive name (e.g. 'Demo TTS', 'ElevenLabs', 'OpenAI TTS')."""
        pass

    @property
    @abstractmethod
    def is_demo(self) -> bool:
        """Flag indicating whether this provider runs locally in demo mode."""
        pass

    @abstractmethod
    def synthesize(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        """
        Synthesize text into speech audio bytes.
        
        Args:
            text: Text to synthesize into speech.
            voice_id: Optional identifier for specific voice archetype or persona style.
            
        Returns:
            TTSResult containing audio bytes, format, and playback duration.
        """
        pass
