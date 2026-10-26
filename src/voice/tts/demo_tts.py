"""
Deterministic Demo Text-to-Speech Provider for Pitch Practice Partner.
Synthesizes valid PCM WAV audio locally using standard-library modules.
Requires zero external credentials, network requests, or third-party audio packages.
"""

import io
import math
import struct
import wave
from typing import Optional

from src.voice.voice_models import TTSResult
from src.voice.provider import TTSProvider


class DemoTTSProvider(TTSProvider):
    """
    Deterministic demo text-to-speech provider.
    Synthesizes clean, valid PCM audio waveforms with standard RIFF/WAVE headers
    compatible with browser playback via Streamlit's st.audio.
    """

    def __init__(self, sample_rate: int = 16000, base_frequency: float = 380.0) -> None:
        """
        Initialize DemoTTSProvider.

        Args:
            sample_rate: Audio sampling rate in Hz (default 16000).
            base_frequency: Synthesis tone frequency in Hz (default 380.0).
        """
        self.sample_rate = sample_rate
        self.base_frequency = base_frequency

    @property
    def name(self) -> str:
        return "Demo TTS (Synthesized Audio)"

    @property
    def is_demo(self) -> bool:
        return True

    def synthesize(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        """
        Synthesize text into a playable WAV audio byte stream.
        Duration scales reasonably with word count (~140 words per minute speaking pace).

        Args:
            text: Input text string to synthesize.
            voice_id: Optional voice archetype identifier.

        Returns:
            TTSResult with valid WAV bytes, duration, and error status.
        """
        try:
            clean_text = text.strip() if text else ""
            if not clean_text:
                # Generate minimal silence (0.2s)
                audio_bytes = self._generate_wav_bytes(duration_sec=0.2, amplitude=0.0)
                return TTSResult(
                    audio_bytes=audio_bytes,
                    audio_format="audio/wav",
                    duration_seconds=0.2,
                    error=None,
                )

            word_count = len(clean_text.split())
            # Estimate ~140 WPM -> ~0.43s per word, bounded between 0.8s and 6.0s for demo responsiveness
            est_duration = max(0.8, min(6.0, word_count * (60.0 / 140.0)))

            # Slightly modulate frequency based on voice_id if provided
            freq = self.base_frequency
            if voice_id and "senior" in voice_id.lower():
                freq = 280.0
            elif voice_id and "friendly" in voice_id.lower():
                freq = 440.0

            audio_bytes = self._generate_wav_bytes(duration_sec=est_duration, amplitude=0.15, frequency=freq)

            return TTSResult(
                audio_bytes=audio_bytes,
                audio_format="audio/wav",
                duration_seconds=round(est_duration, 2),
                error=None,
            )
        except Exception as e:
            return TTSResult(
                audio_bytes=b"",
                audio_format="audio/wav",
                duration_seconds=None,
                error=f"Synthesis error: {str(e)}",
            )

    def _generate_wav_bytes(
        self, duration_sec: float, amplitude: float = 0.15, frequency: Optional[float] = None
    ) -> bytes:
        """
        Generate a valid PCM 16-bit mono WAV byte stream with a standard 44-byte RIFF header.
        """
        freq = frequency or self.base_frequency
        num_frames = int(self.sample_rate * duration_sec)
        buffer = io.BytesIO()

        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)          # Mono
            wav_file.setsampwidth(2)         # 16-bit PCM (2 bytes/sample)
            wav_file.setframerate(self.sample_rate)

            # Soft attack and decay envelope to prevent audio clicking on playback
            fade_frames = min(int(self.sample_rate * 0.05), num_frames // 4)
            frames = bytearray()

            for i in range(num_frames):
                env = 1.0
                if i < fade_frames and fade_frames > 0:
                    env = i / float(fade_frames)
                elif i > (num_frames - fade_frames) and fade_frames > 0:
                    env = (num_frames - i) / float(fade_frames)

                # Pure sine wave with gentle amplitude modulation
                val = amplitude * env * math.sin(2.0 * math.pi * freq * (i / self.sample_rate))
                clamped_val = max(-1.0, min(1.0, val))
                sample_int = int(clamped_val * 32767.0)
                frames.extend(struct.pack("<h", sample_int))

            wav_file.writeframes(frames)

        return buffer.getvalue()
