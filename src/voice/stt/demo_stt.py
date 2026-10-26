"""
Deterministic Demo Speech-to-Text Provider for Pitch Practice Partner.
Operates completely offline without external credentials or network requests.

IMPORTANT:
This provider does NOT pretend to genuinely transcribe arbitrary speech.
Its output is explicitly labeled as a simulated demo transcript for testing
and demonstration of the end-to-end voice simulation workflow.
"""

from typing import Optional
from src.voice.voice_models import AudioData, STTResult
from src.voice.provider import STTProvider


class DemoSTTProvider(STTProvider):
    """
    Deterministic demo speech-to-text provider.
    Validates audio input presence and returns an explicit, clearly labeled
    simulated demo transcript suitable for downstream conversation processing.
    """

    SAMPLE_TRANSCRIPTS = [
        "[DEMO VOICE TRANSCRIPT] I would first understand the client's requirements and then propose a suitable solution.",
        "[DEMO VOICE TRANSCRIPT] In my previous role, our team encountered a critical scalability bottleneck. I took the initiative to refactor our data pipeline, which reduced processing latency by 35% and improved throughput.",
        "[DEMO VOICE TRANSCRIPT] To address this concern, we conducted an empirical trade-off analysis between immediate development velocity and long-term maintenance overhead before settling on our microservice boundary design.",
    ]

    def __init__(self, fixed_transcript: Optional[str] = None) -> None:
        """
        Initialize DemoSTTProvider.

        Args:
            fixed_transcript: Optional custom simulated transcript for deterministic testing.
        """
        self._fixed_transcript = fixed_transcript
        self._invocation_count = 0

    @property
    def name(self) -> str:
        return "Demo STT (Simulated)"

    @property
    def is_demo(self) -> bool:
        return True

    def transcribe(self, audio: AudioData) -> STTResult:
        """
        Produce a simulated transcription for testing and demo practice.
        Explicitly marks simulated nature, sets confidence to None,
        and preserves actual audio duration if known without fabricating values.
        """
        if not audio or not audio.raw_bytes:
            raise ValueError("Cannot transcribe empty audio data.")

        duration = audio.duration_seconds
        if duration is None or duration <= 0.0:
            from src.voice.audio_utils import extract_wav_duration
            wav_dur = extract_wav_duration(audio.raw_bytes)
            if wav_dur is not None and wav_dur > 0.0:
                duration = wav_dur
            else:
                duration = None

        if self._fixed_transcript:
            text = self._fixed_transcript
        else:
            text = self.SAMPLE_TRANSCRIPTS[self._invocation_count % len(self.SAMPLE_TRANSCRIPTS)]
            self._invocation_count += 1

        return STTResult(
            text=text,
            confidence=None,
            duration_seconds=duration,
            is_simulated=True,
            error=None,
        )
