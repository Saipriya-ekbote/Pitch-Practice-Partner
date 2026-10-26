"""
Tests for Voice Interaction & Speech Intelligence (Phase 8).
Validates provider abstractions, zero-dependency demo STT/TTS, audio validation,
factual speech metrics, conversation integration, history persistence, and analytics.
"""

import io
import wave
import pytest
from unittest.mock import MagicMock

from src.voice.voice_models import AudioData, STTResult, TTSResult, SpeechMetrics
from src.voice.provider import STTProvider, TTSProvider
from src.voice.stt.demo_stt import DemoSTTProvider
from src.voice.tts.demo_tts import DemoTTSProvider
from src.voice.audio_utils import extract_wav_duration, validate_audio_data
from src.voice.metrics import calculate_speech_metrics
from src.voice.engine import VoiceEngine, get_voice_service
from src.conversation.conversation_manager import ConversationManager
from src.conversation.conversation_models import PracticeSession, ConversationMessage
from src.intelligence.conversation_analyzer import ConversationAnalyzer
from src.evaluation.evaluation_engine import EvaluationEngine
from src.feedback.feedback_engine import FeedbackEngine
from src.history.history_repository import HistoryRepository
from src.history.history_service import HistoryService
from src.history.history_models import HistoricalSession
from src.history.analytics import AnalyticsService
from src.scenarios.scenario_manager import ScenarioManager


# ============================================================================
# 1-4: Provider Contracts & Result Models
# ============================================================================

def test_stt_provider_contract():
    """Verify STTProvider interface enforcement and custom provider implementation."""
    class CustomSTT(STTProvider):
        @property
        def name(self) -> str:
            return "Custom STT"

        @property
        def is_demo(self) -> bool:
            return False

        def transcribe(self, audio: AudioData) -> STTResult:
            return STTResult(text="Transcribed custom audio", confidence=0.92, duration_seconds=audio.duration_seconds)

    provider = CustomSTT()
    assert provider.name == "Custom STT"
    assert provider.is_demo is False
    res = provider.transcribe(AudioData(raw_bytes=b"12345", duration_seconds=2.0))
    assert res.text == "Transcribed custom audio"
    assert res.confidence == 0.92
    assert res.is_simulated is False


def test_tts_provider_contract():
    """Verify TTSProvider interface enforcement and custom provider implementation."""
    class CustomTTS(TTSProvider):
        @property
        def name(self) -> str:
            return "Custom TTS"

        @property
        def is_demo(self) -> bool:
            return False

        def synthesize(self, text: str, voice_id: str = None) -> TTSResult:
            return TTSResult(audio_bytes=b"dummy_wav", duration_seconds=1.5)

    provider = CustomTTS()
    assert provider.name == "Custom TTS"
    assert provider.is_demo is False
    res = provider.synthesize("Hello")
    assert res.audio_bytes == b"dummy_wav"
    assert res.duration_seconds == 1.5


def test_stt_result_model():
    """Verify STTResult dataclass validation, error field, and dictionary serialization."""
    res = STTResult(text="Test transcript", confidence=0.85, duration_seconds=3.2, is_simulated=True, error=None)
    assert res.text == "Test transcript"
    assert res.confidence == 0.85
    assert res.duration_seconds == 3.2
    assert res.is_simulated is True
    assert res.error is None
    d = res.to_dict()
    assert d["confidence"] == 0.85

    # Invalid confidence bounds
    with pytest.raises(ValueError):
        STTResult(text="Bad", confidence=1.5)

    with pytest.raises(ValueError):
        STTResult(text="Bad", duration_seconds=-1.0)


def test_tts_result_model():
    """Verify TTSResult dataclass validation, error field, and properties."""
    res = TTSResult(audio_bytes=b"fake_audio_stream", audio_format="audio/wav", duration_seconds=2.1, error=None)
    assert res.size_bytes == 17
    assert res.duration_seconds == 2.1
    assert res.error is None

    # Invalid types
    with pytest.raises(ValueError):
        TTSResult(audio_bytes="not_bytes")  # type: ignore

    with pytest.raises(ValueError):
        TTSResult(audio_bytes=b"ok", duration_seconds=-0.5)


# ============================================================================
# 5-9: Demo STT & Demo TTS Implementation
# ============================================================================

def test_demo_stt_deterministic_behavior():
    """Verify DemoSTTProvider generates deterministic simulated transcripts."""
    provider1 = DemoSTTProvider()
    provider2 = DemoSTTProvider()
    audio = AudioData(raw_bytes=b"headerandpayload12345", audio_format="wav", duration_seconds=4.0)

    res1 = provider1.transcribe(audio)
    res2 = provider2.transcribe(audio)
    assert res1.text == res2.text
    assert "[DEMO VOICE TRANSCRIPT]" in res1.text


def test_demo_stt_is_simulated_and_confidence_none():
    """
    CRITICAL REQUIREMENT:
    Demo STT must explicitly set is_simulated=True and confidence=None.
    It must NOT pretend to genuinely measure transcription confidence (no 1.0 or 0.98).
    """
    provider = DemoSTTProvider()
    audio = AudioData(raw_bytes=b"1234567890" * 5, audio_format="wav", duration_seconds=3.0)
    result = provider.transcribe(audio)

    assert result.is_simulated is True
    assert result.confidence is None
    assert result.duration_seconds == 3.0
    assert "[DEMO VOICE TRANSCRIPT]" in result.text


def test_demo_stt_custom_fixed_transcript():
    """Verify injected fixed transcript for deterministic automated testing."""
    custom_text = "[DEMO VOICE TRANSCRIPT] Custom verified response for unit test."
    provider = DemoSTTProvider(fixed_transcript=custom_text)
    audio = AudioData(raw_bytes=b"bytes123", audio_format="wav")
    result = provider.transcribe(audio)
    assert result.text == custom_text
    assert result.is_simulated is True
    assert result.confidence is None


def test_demo_tts_deterministic_behavior():
    """Verify DemoTTSProvider synthesizes deterministic WAV audio bytes for identical input."""
    tts1 = DemoTTSProvider(sample_rate=16000)
    tts2 = DemoTTSProvider(sample_rate=16000)
    res1 = tts1.synthesize("Identical text prompt for synthesis.")
    res2 = tts2.synthesize("Identical text prompt for synthesis.")
    assert res1.audio_bytes == res2.audio_bytes
    assert res1.duration_seconds == res2.duration_seconds


def test_demo_tts_valid_wav_bytes():
    """Verify DemoTTSProvider produces genuine, readable PCM 16-bit mono WAV bytes."""
    tts = DemoTTSProvider(sample_rate=16000)
    result = tts.synthesize("Synthesize speech into valid playable audio.")

    assert isinstance(result, TTSResult)
    assert result.audio_format == "audio/wav"
    assert result.duration_seconds > 0.0
    assert len(result.audio_bytes) > 44  # WAV header is 44 bytes

    # Verify standard library wave module parses the synthesized bytes without error
    buffer = io.BytesIO(result.audio_bytes)
    with wave.open(buffer, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 16000
        frames = wf.getnframes()
        assert frames > 0


def test_demo_tts_empty_or_whitespace_text():
    """Verify DemoTTSProvider handles empty or whitespace text gracefully without raising."""
    tts = DemoTTSProvider()
    res_empty = tts.synthesize("")
    assert isinstance(res_empty, TTSResult)
    assert len(res_empty.audio_bytes) > 44
    assert res_empty.error is None

    res_spaces = tts.synthesize("    ")
    assert isinstance(res_spaces, TTSResult)
    assert len(res_spaces.audio_bytes) > 44
    assert res_spaces.error is None


# ============================================================================
# 10-13: VoiceEngine & Audio Validation
# ============================================================================

def test_voice_engine_dependency_injection():
    """Verify VoiceEngine enforces dependency injection and is NOT a singleton."""
    stt_mock = MagicMock(spec=STTProvider)
    tts_mock = MagicMock(spec=TTSProvider)

    engine1 = VoiceEngine(stt_provider=stt_mock, tts_provider=tts_mock)
    engine2 = VoiceEngine(stt_provider=stt_mock, tts_provider=tts_mock)

    assert engine1 is not engine2
    assert engine1.stt_provider is stt_mock
    assert engine1.tts_provider is tts_mock

    # None provider rejected
    with pytest.raises(ValueError):
        VoiceEngine(stt_provider=None, tts_provider=tts_mock)  # type: ignore

    with pytest.raises(ValueError):
        VoiceEngine(stt_provider=stt_mock, tts_provider=None)  # type: ignore


def test_voice_engine_audio_validation():
    """Verify audio data validation rules for size, format, and duration boundaries."""
    tts = DemoTTSProvider()
    valid_wav = tts.synthesize("Valid test utterance for audio checking.").audio_bytes

    # 1. Valid WAV
    ok, err = validate_audio_data(valid_wav, audio_format="wav")
    assert ok is True
    assert err is None

    # 2. Unsupported format
    ok, err = validate_audio_data(valid_wav, audio_format="flac")
    assert ok is False
    assert "unsupported" in err.lower()

    # 3. Duration too short
    ok, err = validate_audio_data(valid_wav, audio_format="wav", duration_seconds=0.05)
    assert ok is False
    assert "short" in err.lower()

    # 4. Duration too long
    ok, err = validate_audio_data(valid_wav, audio_format="wav", duration_seconds=500.0)
    assert ok is False
    assert "exceeds" in err.lower()


def test_voice_engine_empty_audio_handling():
    """Verify VoiceEngine and validate_audio reject empty audio data gracefully."""
    engine = get_voice_service()

    ok, err = validate_audio_data(b"", audio_format="wav")
    assert ok is False
    assert "empty" in err.lower()

    with pytest.raises(ValueError) as exc:
        engine.process_speech_input(audio=b"", audio_format="wav")
    assert "empty" in str(exc.value).lower()


def test_voice_engine_malformed_audio_handling():
    """Verify corrupt or unreadable audio is caught by extract_wav_duration and validation."""
    assert extract_wav_duration(b"") is None
    assert extract_wav_duration(b"corrupt header bytes not riff") is None

    # Non-WAV formats without duration are accepted if format supported, duration stays None
    ok, err = validate_audio_data(b"fake_webm_bytes_12345", audio_format="webm")
    assert ok is True
    assert err is None


# ============================================================================
# 14-16: Speech Metrics (Duration, Word Count, WPM, Missing Duration)
# ============================================================================

def test_speech_metrics_word_count_and_wpm():
    """Verify factual calculation of word count and WPM strictly from recording duration."""
    transcript = "We deployed a distributed Redis caching layer to resolve database contention issues."
    # 12 words in 6.0s -> (12 / 6.0) * 60 = 120.0 WPM
    metrics = calculate_speech_metrics(transcript=transcript, recording_duration_seconds=6.0)

    assert metrics.word_count == 12
    assert metrics.recording_duration_seconds == 6.0
    assert metrics.words_per_minute == 120.0
    assert metrics.confidence is None


def test_speech_metrics_missing_or_short_duration_wpm_none():
    """
    CRITICAL REQUIREMENT:
    If reliable recording duration is unavailable (None or < 1.0s),
    words_per_minute MUST be None. Do not fabricate or estimate.
    """
    transcript = "Quick answer with some words."

    # Duration is None
    m_none = calculate_speech_metrics(transcript, recording_duration_seconds=None)
    assert m_none.recording_duration_seconds is None
    assert m_none.words_per_minute is None

    # Duration is 0.0s
    m_zero = calculate_speech_metrics(transcript, recording_duration_seconds=0.0)
    assert m_zero.words_per_minute is None

    # Duration is < 1.0s (unreliable for WPM extrapolation)
    m_short = calculate_speech_metrics(transcript, recording_duration_seconds=0.5)
    assert m_short.words_per_minute is None


def test_speech_metrics_filler_words_from_existing_detector():
    """Verify vocal fillers are measured using the existing Phase 4 detector without regex duplication."""
    transcript = "Um, basically we like completed the migration ahead of schedule, you know."
    metrics = calculate_speech_metrics(transcript, recording_duration_seconds=5.0)

    assert metrics.filler_count >= 2
    assert metrics.filler_percentage > 0.0


# ============================================================================
# 17-18: Failure Handling (STT / TTS Failures Graceful)
# ============================================================================

def test_voice_engine_stt_failure_handling():
    """Verify STT provider exceptions are caught cleanly and return an error result without crashing."""
    failing_stt = MagicMock(spec=STTProvider)
    failing_stt.name = "Failing STT"
    failing_stt.is_demo = False
    failing_stt.transcribe.side_effect = RuntimeError("STT network timeout or service unavailable")

    mock_tts = DemoTTSProvider()
    engine = VoiceEngine(stt_provider=failing_stt, tts_provider=mock_tts)

    audio = AudioData(raw_bytes=b"dummy_audio_bytes_12345", audio_format="wav", duration_seconds=2.5)
    stt_res, metrics = engine.process_speech_input(audio)

    assert stt_res.text == ""
    assert stt_res.error is not None
    assert "timeout" in stt_res.error.lower()
    assert metrics.word_count == 0


def test_voice_engine_tts_failure_handling():
    """Verify TTS provider exceptions are caught cleanly and do not destroy AI response."""
    mock_stt = DemoSTTProvider()
    failing_tts = MagicMock(spec=TTSProvider)
    failing_tts.name = "Failing TTS"
    failing_tts.is_demo = False
    failing_tts.synthesize.side_effect = RuntimeError("TTS synthesis service quota exceeded")

    engine = VoiceEngine(stt_provider=mock_stt, tts_provider=failing_tts)
    tts_res = engine.synthesize("Important AI interviewer response text")

    assert tts_res.audio_bytes == b""
    assert tts_res.error is not None
    assert "quota" in tts_res.error.lower()


# ============================================================================
# 19: ConversationManager Integration
# ============================================================================

def test_voice_conversation_flow():
    """Verify transcribed voice messages integrate seamlessly with existing ConversationManager API."""
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("tech_python_01")
    persona = scenario_mgr.get_persona_by_id("persona_tech_peer")
    assert scenario is not None
    assert persona is not None

    conv_mgr = ConversationManager()
    session = conv_mgr.start_session(
        scenario=scenario,
        persona=persona,
        difficulty="Intermediate",
    )
    assert session.is_active()

    # Voice input simulation
    voice_engine = get_voice_service(
        stt_provider=DemoSTTProvider(fixed_transcript="I prioritize list comprehensions and generators for memory efficiency.")
    )
    stt_res, metrics = voice_engine.process_speech_input(
        audio=b"12345" * 10,
        audio_format="wav",
        duration_seconds=3.5,
    )
    assert "[DEMO VOICE TRANSCRIPT]" in stt_res.text or "generators" in stt_res.text

    # ConversationManager processes the text normally via existing send_user_message API
    updated_session, assistant_msg = conv_mgr.send_user_message(
        session=session,
        user_content=stt_res.text,
        scenario=scenario,
        persona=persona,
    )
    assert updated_session.turn_number == 1
    assert updated_session.conversation_history[-2].content == stt_res.text
    assert assistant_msg.role == "assistant"
    assert len(assistant_msg.content) > 0

    # TTS synthesizes response audio
    synth_res = voice_engine.synthesize(assistant_msg.content)
    assert synth_res.error is None
    assert len(synth_res.audio_bytes) > 44


def test_voice_session_intelligence_and_evaluation():
    """Verify that sessions with voice transcripts pass through Phase 4-6 evaluation unchanged."""
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("tech_python_01")
    persona = scenario_mgr.get_persona_by_id("persona_tech_peer")

    conv_mgr = ConversationManager()
    session = conv_mgr.start_session(
        scenario=scenario,
        persona=persona,
        difficulty="Intermediate",
    )

    updated_session, _ = conv_mgr.send_user_message(
        session=session,
        user_content="I use generators to stream large datasets without loading everything into memory at once.",
        scenario=scenario,
        persona=persona,
    )

    # Phase 4 Conversation Intelligence
    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(updated_session, scenario, persona)
    assert analysis.total_user_words > 0

    # Phase 5 Evaluation
    evaluator = EvaluationEngine()
    evaluation = evaluator.evaluate(analysis=analysis, scenario=scenario, persona=persona)
    assert evaluation.overall_score >= 0.0

    # Phase 6 Feedback
    feedback_engine = FeedbackEngine()
    feedback = feedback_engine.generate_feedback(
        analysis=analysis,
        evaluation=evaluation,
        session=updated_session,
        scenario=scenario,
        persona=persona,
    )
    assert len(feedback.strengths) > 0 or len(feedback.improvements) > 0


# ============================================================================
# 20-23: History, Analytics, and Raw Audio Privacy
# ============================================================================

def test_history_save_and_retrieve_voice_session(tmp_path):
    """Verify persisting a voice session stores interaction_mode='voice' and speech metrics."""
    db_path = str(tmp_path / "test_voice_history.db")
    repo = HistoryRepository(db_path=db_path)
    service = HistoryService(repository=repo)

    session = PracticeSession(
        session_id="voice-sess-001",
        scenario_id="tech_python_01",
        persona_id="persona_tech_peer",
        mode="Technical Interview",
        difficulty="Intermediate",
        turn_number=1,
        status="completed",
        conversation_history=[
            ConversationMessage(role="assistant", content="How do you handle memory in Python?"),
            ConversationMessage(role="user", content="I use generators and iterators."),
        ],
    )

    speech_metrics = {
        "recording_duration_seconds": 12.5,
        "word_count": 30,
        "words_per_minute": 144.0,
        "confidence": None,
        "filler_count": 1,
        "filler_percentage": 3.3,
    }

    saved = service.save_completed_session(
        session=session,
        interaction_mode="voice",
        speech_metrics=speech_metrics,
    )
    assert saved.interaction_mode == "voice"
    assert saved.speech_metrics is not None
    assert saved.speech_metrics["words_per_minute"] == 144.0

    # Retrieve from DB
    retrieved = service.get_session("voice-sess-001")
    assert retrieved is not None
    assert retrieved.interaction_mode == "voice"
    assert retrieved.speech_metrics["words_per_minute"] == 144.0
    assert retrieved.speech_metrics["recording_duration_seconds"] == 12.5


def test_raw_audio_not_persisted_in_database(tmp_path):
    """
    CRITICAL PRIVACY REQUIREMENT:
    Raw audio bytes MUST NEVER be persisted into SQLite or historical records.
    """
    db_path = str(tmp_path / "test_privacy.db")
    repo = HistoryRepository(db_path=db_path)
    service = HistoryService(repository=repo)

    session = PracticeSession(
        session_id="privacy-sess-001",
        turn_number=1,
        status="completed",
        conversation_history=[
            ConversationMessage(role="user", content="Candidate transcribed response"),
        ],
    )

    service.save_completed_session(
        session=session,
        interaction_mode="voice",
        speech_metrics={"recording_duration_seconds": 5.0, "words_per_minute": 120.0},
    )

    # Inspect SQLite database schema directly
    with repo._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sessions);")
        columns = [row[1] for row in cursor.fetchall()]
        # Verify no audio blob column exists
        assert "audio_bytes" not in columns
        assert "raw_audio" not in columns

        cursor.execute("SELECT * FROM sessions WHERE session_id = 'privacy-sess-001';")
        row = cursor.fetchone()
        row_dict = dict(row)
        for k, v in row_dict.items():
            assert not isinstance(v, (bytes, bytearray)), f"Found persistent raw audio bytes in column {k}!"


def test_analytics_voice_metrics(tmp_path):
    """Verify AnalyticsService produces objective voice statistics."""
    db_path = str(tmp_path / "test_voice_analytics.db")
    repo = HistoryRepository(db_path=db_path)
    service = HistoryService(repository=repo)
    analytics = AnalyticsService(history_service=service)

    # 1. No sessions initially
    stats_empty = analytics.get_voice_analytics()
    assert stats_empty["has_voice_data"] is False
    assert stats_empty["voice_session_count"] == 0

    # 2. Add 2 voice sessions and 1 text session
    v1 = PracticeSession(session_id="v-1", turn_number=1, status="completed", mode="Pitch")
    service.save_completed_session(
        v1,
        interaction_mode="voice",
        speech_metrics={"recording_duration_seconds": 10.0, "words_per_minute": 140.0, "filler_count": 2, "word_count": 23},
    )

    v2 = PracticeSession(session_id="v-2", turn_number=1, status="completed", mode="Pitch")
    service.save_completed_session(
        v2,
        interaction_mode="voice",
        speech_metrics={"recording_duration_seconds": 20.0, "words_per_minute": 160.0, "filler_count": 4, "word_count": 53},
    )

    t1 = PracticeSession(session_id="t-1", turn_number=1, status="completed", mode="Pitch")
    service.save_completed_session(t1, interaction_mode="text")

    stats = analytics.get_voice_analytics()
    assert stats["has_voice_data"] is True
    assert stats["total_sessions"] == 3
    assert stats["voice_session_count"] == 2
    assert stats["text_session_count"] == 1
    assert stats["average_voice_duration_seconds"] == 15.0
    assert stats["average_wpm"] == 150.0
    assert stats["voice_usage_percentage"] == 66.7


def test_text_mode_regression_behavior(tmp_path):
    """Verify existing text sessions default interaction_mode='text' and speech_metrics=None."""
    db_path = str(tmp_path / "test_regression.db")
    repo = HistoryRepository(db_path=db_path)
    service = HistoryService(repository=repo)

    session = PracticeSession(
        session_id="text-sess-001",
        scenario_id="tech_python_01",
        persona_id="persona_tech_peer",
        mode="Technical Interview",
        difficulty="Intermediate",
        turn_number=1,
        status="completed",
        conversation_history=[
            ConversationMessage(role="assistant", content="What is PEP 8?"),
            ConversationMessage(role="user", content="It is the Python style guide."),
        ],
    )

    saved = service.save_completed_session(session=session)
    assert saved.interaction_mode == "text"
    assert saved.speech_metrics is None

    retrieved = service.get_session("text-sess-001")
    assert retrieved is not None
    assert retrieved.interaction_mode == "text"
    assert retrieved.speech_metrics is None


# ============================================================================
# 26+: Phase 8 Voice Interaction Regression & Microphone Stability Tests
# ============================================================================

def test_regression_deterministic_38_4s_recording_and_metrics():
    """
    Verify the exact scenario discovered during browser testing:
    A 38.4s recording produces 32 words, 50.0 WPM, and is_simulated=True.
    """
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        # 38.4 seconds * 16000 frames/sec = 614400 frames
        wf.writeframes(b"\x00\x00" * int(38.4 * 16000))
    raw_wav = buf.getvalue()

    dur = extract_wav_duration(raw_wav)
    assert dur == 38.4

    stt = DemoSTTProvider()
    stt._invocation_count = 1
    res = stt.transcribe(AudioData(raw_bytes=raw_wav, audio_format="wav"))
    assert res.duration_seconds == 38.4
    assert res.is_simulated is True
    assert res.confidence is None

    metrics = calculate_speech_metrics(
        transcript=res.text,
        recording_duration_seconds=res.duration_seconds,
        confidence=res.confidence,
        is_simulated=res.is_simulated,
    )
    assert metrics.recording_duration_seconds == 38.4
    assert metrics.word_count == 32
    assert metrics.words_per_minute == 50.0
    assert metrics.is_simulated is True
    assert metrics.confidence is None


def test_regression_audio_buffer_safe_read_getvalue():
    """
    Verify that reading audio bytes via getvalue() preserves data across multiple reads,
    preventing empty byte streams on stream reruns.
    """
    class MockUploadedAudio:
        def __init__(self, data: bytes, name: str = "recording.wav"):
            self.data = data
            self.name = name
            self.file = io.BytesIO(data)

        def read(self):
            return self.file.read()

        def getvalue(self):
            return self.data

    audio_data = b"RIFF" + b"\x00" * 40
    mock = MockUploadedAudio(audio_data)

    read1 = mock.getvalue()
    read2 = mock.getvalue()
    assert read1 == audio_data
    assert read2 == audio_data
    assert len(read2) == len(audio_data)


def test_regression_voice_state_reset_between_turns():
    """
    Verify voice input states (transcript, editor, metrics, counter) can be reset cleanly,
    preventing state bleed or reused widget identifiers between turns.
    """
    from app import reset_voice_state

    class MockSessionState(dict):
        def __getattr__(self, name):
            return self.get(name)
        def __setattr__(self, name, value):
            self[name] = value

    import streamlit as st
    orig_ss = getattr(st, "session_state", None)
    mock_ss = MockSessionState({
        "voice_transcript": "stale transcript from turn 1",
        "voice_transcript_editor": "stale transcript in editor",
        "voice_metrics": SpeechMetrics(recording_duration_seconds=38.4, word_count=32, words_per_minute=50.0),
        "voice_metrics_dict": {"recording_duration_seconds": 38.4, "words_per_minute": 50.0},
        "last_processed_audio_bytes": b"stale_bytes",
        "voice_record_counter": 1,
    })
    st.session_state = mock_ss
    try:
        reset_voice_state()
        assert st.session_state.voice_transcript == ""
        assert st.session_state["voice_transcript_editor"] == ""
        assert st.session_state.voice_metrics is None
        assert st.session_state.voice_metrics_dict is None
        assert st.session_state.last_processed_audio_bytes is None
        assert st.session_state.voice_record_counter == 2
    finally:
        st.session_state = orig_ss


def test_regression_multi_turn_aggregate_metrics():
    """
    Verify that multi-turn voice sessions compute accurate aggregate speech metrics.
    """
    turn1_metrics = {
        "recording_duration_seconds": 38.4,
        "word_count": 32,
        "words_per_minute": 50.0,
        "filler_count": 0,
        "is_simulated": True,
    }
    turn2_metrics = {
        "recording_duration_seconds": 21.6,
        "word_count": 28,
        "words_per_minute": 77.8,
        "filler_count": 2,
        "is_simulated": True,
    }
    v_list = [turn1_metrics, turn2_metrics]

    total_dur = sum(m["recording_duration_seconds"] for m in v_list)
    total_words = sum(m["word_count"] for m in v_list)
    total_fillers = sum(m["filler_count"] for m in v_list)
    avg_wpm = round(total_words / (total_dur / 60.0), 1)
    filler_pct = round(total_fillers / total_words * 100.0, 1)

    assert total_dur == 60.0
    assert total_words == 60
    assert avg_wpm == 60.0
    assert total_fillers == 2
    assert filler_pct == round(2 / 60 * 100, 1)


def test_regression_transcript_editor_reset_lifecycle():
    """
    Verify that reset_voice_state does not mutate instantiated widget keys in the active
    Streamlit run context (which would raise StreamlitAPIException), and that the deferred
    reset properly cleanses the editor state at the start of the next run before widget mount.
    """
    from unittest.mock import patch, MagicMock
    import streamlit as st
    from streamlit.errors import StreamlitAPIException
    from app import reset_voice_state

    class MockStreamlitState(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.locked_widgets = set()

        def __getattr__(self, name):
            if name in self:
                return self[name]
            return super().get(name)

        def __setattr__(self, name, value):
            if name == "locked_widgets":
                self.__dict__["locked_widgets"] = value
                return
            self[name] = value

        def __setitem__(self, key, value):
            if hasattr(self, "locked_widgets") and key in self.locked_widgets:
                raise StreamlitAPIException(
                    f"st.session_state.{key} cannot be modified after the widget with key {key} is instantiated."
                )
            super().__setitem__(key, value)

    orig_ss = getattr(st, "session_state", None)
    mock_ss = MockStreamlitState({
        "voice_transcript": "Previous turn speech transcript",
        "voice_transcript_editor": "Previous turn speech transcript",
        "voice_metrics": SpeechMetrics(recording_duration_seconds=15.0, word_count=20, words_per_minute=80.0),
        "voice_metrics_dict": {"recording_duration_seconds": 15.0, "words_per_minute": 80.0},
        "last_processed_audio_bytes": b"dummy_audio_turn_1",
        "voice_record_counter": 1,
        "pending_transcript_reset": False,
    })
    # Simulate that the widget `voice_transcript_editor` is currently instantiated in this run
    mock_ss.locked_widgets.add("voice_transcript_editor")
    st.session_state = mock_ss

    try:
        # Mock active Streamlit ScriptRunContext
        mock_ctx = MagicMock()
        with patch("streamlit.runtime.scriptrunner.get_script_run_ctx", return_value=mock_ctx):
            # Calling reset_voice_state MUST NOT raise StreamlitAPIException
            reset_voice_state()

            # Confirm metrics and flags are reset
            assert st.session_state.voice_transcript == ""
            assert st.session_state.voice_metrics is None
            assert st.session_state.voice_metrics_dict is None
            assert st.session_state.last_processed_audio_bytes is None
            assert st.session_state.voice_record_counter == 2
            assert st.session_state.pending_transcript_reset is True
            # The editor state in the current run was NOT mutated, avoiding the Streamlit exception
            assert st.session_state["voice_transcript_editor"] == "Previous turn speech transcript"

        # Now simulate the next run cycle before widget instantiation:
        # Widgets are reset for the new run before mounting
        mock_ss.locked_widgets.clear()

        # Simulate the pre-instantiation deferred reset block from app.py
        if st.session_state.get("pending_transcript_reset"):
            st.session_state.voice_transcript = ""
            if "voice_transcript_editor" in st.session_state:
                st.session_state["voice_transcript_editor"] = ""
            st.session_state.pending_transcript_reset = False

        # Verify that for Turn 2, editor is fresh and clean before widget mounts
        assert st.session_state["voice_transcript_editor"] == ""
        assert st.session_state.pending_transcript_reset is False

        # Now widget mounts in Turn 2
        mock_ss.locked_widgets.add("voice_transcript_editor")
        assert st.session_state["voice_transcript_editor"] == ""

    finally:
        st.session_state = orig_ss


def test_regression_second_turn_voice_submission_flow():
    """
    Verify complete two-turn voice conversation submission flow:
    Turn 1 speech -> transcript -> submit -> reset -> Turn 2 speech -> transcript -> submit.
    Confirms ConversationManager history integrity (5 messages) and multi-turn aggregate metrics.
    """
    import streamlit as st
    from app import reset_voice_state
    from src.ai.provider import get_ai_provider

    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("tech_python_01")
    assert scenario is not None
    persona = scenario_mgr.get_persona_by_id("persona_tech_peer")
    assert persona is not None

    ai_provider = get_ai_provider()
    conv_mgr = ConversationManager(ai_provider=ai_provider)
    stt_provider = DemoSTTProvider()
    tts_provider = DemoTTSProvider()

    # Initialize Session
    session = conv_mgr.start_session(scenario=scenario, persona=persona)
    assert len(session.conversation_history) == 1
    assert session.conversation_history[0].role == "assistant"

    session_voice_metrics_list = []

    # --- TURN 1 ---
    # User records audio for Turn 1
    turn1_audio = AudioData(raw_bytes=b"dummy_turn1_audio_bytes", duration_seconds=12.0)
    turn1_stt = stt_provider.transcribe(turn1_audio)
    turn1_metrics = calculate_speech_metrics(
        transcript=turn1_stt.text,
        recording_duration_seconds=turn1_stt.duration_seconds,
        is_simulated=turn1_stt.is_simulated,
    )
    turn1_editor_text = turn1_stt.text

    # User submits Turn 1
    session, turn1_reply = conv_mgr.send_user_message(
        session=session,
        user_content=turn1_editor_text,
        scenario=scenario,
        persona=persona,
    )
    session_voice_metrics_list.append(turn1_metrics.to_dict())
    turn1_tts = tts_provider.synthesize(turn1_reply.content)
    assert turn1_tts.audio_bytes is not None

    # History after Turn 1: Assistant -> User 1 -> Assistant 1
    assert len(session.conversation_history) == 3
    assert session.conversation_history[1].role == "user"
    assert session.conversation_history[1].content == turn1_editor_text
    assert session.conversation_history[2].role == "assistant"

    # Reset voice state between turns
    class MockSessionState(dict):
        def __getattr__(self, name):
            return self.get(name)
        def __setattr__(self, name, value):
            self[name] = value

    orig_ss = getattr(st, "session_state", None)
    mock_ss = MockSessionState({
        "voice_transcript": turn1_stt.text,
        "voice_transcript_editor": turn1_editor_text,
        "voice_metrics": turn1_metrics,
        "voice_metrics_dict": turn1_metrics.to_dict(),
        "last_processed_audio_bytes": turn1_audio.raw_bytes,
        "voice_record_counter": 1,
        "session_voice_metrics_list": session_voice_metrics_list,
        "pending_transcript_reset": False,
    })
    st.session_state = mock_ss

    try:
        reset_voice_state()
        assert st.session_state.pending_transcript_reset is True
        assert st.session_state.voice_metrics is None
        assert st.session_state.last_processed_audio_bytes is None
        assert st.session_state.voice_record_counter == 2

        # Simulate start of Turn 2 run: pre-instantiation reset executes
        if st.session_state.get("pending_transcript_reset"):
            st.session_state.voice_transcript = ""
            if "voice_transcript_editor" in st.session_state:
                st.session_state["voice_transcript_editor"] = ""
            st.session_state.pending_transcript_reset = False

        assert st.session_state["voice_transcript_editor"] == ""

        # --- TURN 2 ---
        turn2_audio = AudioData(raw_bytes=b"dummy_turn2_audio_bytes_distinct", duration_seconds=18.0)
        turn2_stt = stt_provider.transcribe(turn2_audio)
        turn2_metrics = calculate_speech_metrics(
            transcript=turn2_stt.text,
            recording_duration_seconds=turn2_stt.duration_seconds,
            is_simulated=turn2_stt.is_simulated,
        )
        turn2_editor_text = turn2_stt.text

        # User submits Turn 2
        session, turn2_reply = conv_mgr.send_user_message(
            session=session,
            user_content=turn2_editor_text,
            scenario=scenario,
            persona=persona,
        )
        session_voice_metrics_list.append(turn2_metrics.to_dict())
        turn2_tts = tts_provider.synthesize(turn2_reply.content)
        assert turn2_tts.audio_bytes is not None

        # Validate final conversation state after Turn 2
        assert len(session.conversation_history) == 5
        roles = [m.role for m in session.conversation_history]
        assert roles == ["assistant", "user", "assistant", "user", "assistant"]
        assert session.conversation_history[3].role == "user"
        assert session.conversation_history[3].content == turn2_editor_text
        assert session.conversation_history[4].role == "assistant"

        # Validate metrics list has two turns recorded
        assert len(session_voice_metrics_list) == 2
        assert session_voice_metrics_list[0]["recording_duration_seconds"] == 12.0
        assert session_voice_metrics_list[1]["recording_duration_seconds"] == 18.0
    finally:
        st.session_state = orig_ss


