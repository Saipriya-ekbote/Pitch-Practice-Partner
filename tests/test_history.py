"""
Unit and integration tests for Phase 7: Session History & Persistence.
Covers SQLite repository, service logic, data models, transcript filtering,
evaluation/feedback fidelity, idempotency, and edge cases.
"""

import os
import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from typing import List

from src.scenarios.scenario_models import Scenario, Persona
from src.conversation.conversation_models import (
    PracticeSession,
    ConversationMessage,
    MessageRole,
    SessionStatus,
)
from src.evaluation.evaluation_models import (
    EvaluationResult,
    ScoreDimension,
    DimensionStatus,
)
from src.feedback.feedback_models import (
    FeedbackResult,
    FeedbackItem,
    StrengthFeedbackItem,
    ImprovementFeedbackItem,
    PracticeAction,
    FeedbackPriority,
    EvidenceType,
)
from src.history import (
    HistoricalSession,
    HistoricalMessage,
    HistoricalDimensionScore,
    HistoryRepository,
    HistoryService,
    evaluation_from_dict,
    feedback_from_dict,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for isolated testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def repository(temp_db_path):
    """Instantiate a repository backed by a clean temporary database."""
    return HistoryRepository(db_path=temp_db_path)


@pytest.fixture
def history_service(repository):
    """Instantiate HistoryService with the test repository."""
    return HistoryService(repository=repository)


@pytest.fixture
def sample_scenario():
    return Scenario(
        id="tech_sys_design",
        name="Distributed Systems Architecture",
        mode="Technical Interview",
        difficulty="Intermediate",
        description="Design a scalable message queue.",
        expected_topics=["Partitioning", "Replication", "Throughput"],
    )


@pytest.fixture
def sample_persona():
    return Persona(
        id="tech_lead",
        name="Alex Chen",
        role="Principal Infrastructure Architect",
        personality="Analytical, focused",
        background="Experienced distributed systems architect",
        objective="Evaluate systems design depth",
        knowledge_level="Expert",
        communication_style="Direct, probing",
        difficulty="Intermediate",
    )


@pytest.fixture
def sample_session():
    now = datetime.now(timezone.utc)
    started_at = (now - timedelta(minutes=5)).isoformat()
    ended_at = now.isoformat()

    session = PracticeSession(
        session_id="test-session-12345",
        scenario_id="tech_sys_design",
        persona_id="tech_lead",
        mode="Technical Interview",
        difficulty="Intermediate",
        turn_number=3,
        max_turns=5,
        started_at=started_at,
        ended_at=ended_at,
        status=SessionStatus.COMPLETED.value,
    )
    # Add messages: system message, persona opening, user answer, persona follow-up, user answer
    session.conversation_history = [
        ConversationMessage(
            role="system",
            content="Internal system prompt for Alex Chen.",
            timestamp=(now - timedelta(minutes=4, seconds=55)).isoformat(),
        ),
        ConversationMessage(
            role="assistant",
            content="Let's start by exploring how you partition your queue.",
            timestamp=(now - timedelta(minutes=4, seconds=50)).isoformat(),
        ),
        ConversationMessage(
            role="user",
            content="We use a hash of the partition key modulo the partition count.",
            timestamp=(now - timedelta(minutes=3)).isoformat(),
        ),
        ConversationMessage(
            role="assistant",
            content="How do you handle consumer group rebalancing?",
            timestamp=(now - timedelta(minutes=2)).isoformat(),
        ),
        ConversationMessage(
            role="user",
            content="We use an eager rebalance protocol with heartbeat coordination.",
            timestamp=(now - timedelta(minutes=1)).isoformat(),
        ),
    ]
    return session


@pytest.fixture
def sample_evaluation():
    dim1 = ScoreDimension(
        name="Question Handling",
        score=82.0,
        max_score=100.0,
        weight=1.0,
        status="evaluated",
        evidence=["Candidate directly answered hash partitioning and rebalancing."],
        rationale="Strong direct answers with appropriate technical depth.",
    )
    dim2 = ScoreDimension(
        name="Technical Communication",
        score=78.5,
        max_score=100.0,
        weight=1.0,
        status="evaluated",
        evidence=["Minimal filler words, clear terminology."],
        rationale="Clear phrasing with concise sentences.",
    )
    return EvaluationResult(
        session_id="test-session-12345",
        mode="Technical Interview",
        difficulty="Intermediate",
        overall_score=80.2,
        max_score=100.0,
        dimensions=[dim1, dim2],
        strengths=["Clear technical explanations", "Concrete architecture choices"],
        improvement_areas=["Elaborate on edge cases during failover"],
        insufficient_evidence_dimensions=[],
    )


@pytest.fixture
def sample_feedback():
    item1 = FeedbackItem(
        dimension="Question Handling",
        status="evaluated",
        what="You provided immediate, specific answers to partitioning questions.",
        why="Direct technical precision demonstrates architectural clarity.",
        evidence="\"We use a hash of the partition key modulo the partition count.\"",
        impact="In technical interviews, crisp answers build immediate interviewer trust.",
        action="Maintain this structured pattern when answering failover questions.",
        score=82.0,
        max_score=100.0,
        priority=FeedbackPriority.HIGH.value,
        evidence_type=EvidenceType.TRANSCRIPT_EXCERPT.value,
        source_reference="Turn 1",
    )
    strength1 = StrengthFeedbackItem(
        title="Direct Architecture Explanations",
        what="Consistently started responses with architectural mechanisms.",
        evidence="\"We use an eager rebalance protocol with heartbeat coordination.\"",
        impact="Allows the interviewer to immediately verify competence.",
        evidence_type=EvidenceType.TRANSCRIPT_EXCERPT.value,
        source_reference="Turn 2",
    )
    imp1 = ImprovementFeedbackItem(
        title="Failover Edge Cases",
        what="Consumer failover guarantees were not explicitly articulated.",
        why="Architectural assessments look for edge-case resilience.",
        evidence="[Analysis observation]: Edge case coverage: Unaddressed",
        impact="Leaves ambiguity regarding data consistency during network splits.",
        action="State your split-brain mitigation strategy alongside partitioning.",
        priority=FeedbackPriority.HIGH.value,
        evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
    )
    action1 = PracticeAction(
        title="State Edge Cases First",
        action="Always articulate failure mode mitigations when describing distributed protocols.",
        scenario_context="Technical System Design",
        priority=FeedbackPriority.HIGH.value,
    )
    return FeedbackResult(
        session_id="test-session-12345",
        mode="Technical Interview",
        difficulty="Intermediate",
        overall_summary="Solid technical demonstration with direct responses.",
        items=[item1],
        strengths=[strength1],
        improvements=[imp1],
        priority_actions=[action1],
    )


# --- 1. Database Initialization Tests ---

def test_repository_initialization(temp_db_path):
    """Verify tables and indices are created cleanly upon repository initialization."""
    repo = HistoryRepository(db_path=temp_db_path)
    assert os.path.exists(temp_db_path)
    assert repo.count_sessions() == 0


def test_in_memory_repository():
    """Verify repository functions with in-memory SQLite for testing."""
    repo = HistoryRepository(db_path=":memory:")
    assert repo.count_sessions() == 0


# --- 2. Session Persistence Tests ---

def test_save_and_retrieve_session(history_service, sample_session, sample_scenario, sample_persona, sample_evaluation, sample_feedback):
    """Test saving a completed session and retrieving it with 100% data fidelity."""
    saved = history_service.save_completed_session(
        session=sample_session,
        scenario=sample_scenario,
        persona=sample_persona,
        evaluation=sample_evaluation,
        feedback=sample_feedback,
    )
    assert saved.session_id == sample_session.session_id
    assert saved.turn_count == 3
    assert saved.overall_score == 80.2

    # Retrieve from DB
    retrieved = history_service.get_session(sample_session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == sample_session.session_id
    assert retrieved.mode == "Technical Interview"
    assert retrieved.difficulty == "Intermediate"
    assert retrieved.scenario_name == "Distributed Systems Architecture"
    assert retrieved.persona_name == "Alex Chen"
    assert retrieved.overall_score == 80.2
    assert retrieved.duration_seconds is not None
    assert retrieved.duration_seconds > 0

    # Verify dimensions
    assert len(retrieved.dimensions) == 2
    dim_names = [d.name for d in retrieved.dimensions]
    assert "Question Handling" in dim_names
    assert "Technical Communication" in dim_names

    # Verify evaluation reconstruction
    assert retrieved.evaluation is not None
    assert retrieved.evaluation.overall_score == 80.2
    assert len(retrieved.evaluation.strengths) == 2

    # Verify feedback reconstruction
    assert retrieved.feedback is not None
    assert retrieved.feedback.overall_summary == "Solid technical demonstration with direct responses."
    assert len(retrieved.feedback.strengths) == 1
    assert retrieved.feedback.strengths[0].title == "Direct Architecture Explanations"
    assert len(retrieved.feedback.improvements) == 1
    assert retrieved.feedback.improvements[0].title == "Failover Edge Cases"


def test_idempotent_duplicate_save(history_service, sample_session, sample_scenario, sample_persona, sample_evaluation, sample_feedback):
    """Verify saving the same session multiple times does not duplicate records."""
    s1 = history_service.save_completed_session(
        session=sample_session,
        scenario=sample_scenario,
        persona=sample_persona,
        evaluation=sample_evaluation,
        feedback=sample_feedback,
    )
    # Attempt second save
    s2 = history_service.save_completed_session(
        session=sample_session,
        scenario=sample_scenario,
        persona=sample_persona,
        evaluation=sample_evaluation,
        feedback=sample_feedback,
    )
    assert s1.session_id == s2.session_id
    assert history_service.count_sessions() == 1


def test_cannot_save_unstarted_session(history_service, sample_scenario, sample_persona, sample_evaluation):
    """Verify that unstarted/empty sessions cannot be saved as completed history."""
    empty_session = PracticeSession(
        session_id="empty-session-1",
        status=SessionStatus.NOT_STARTED.value,
        turn_number=0,
    )
    with pytest.raises(ValueError, match="Cannot save an unstarted"):
        history_service.save_completed_session(
            session=empty_session,
            scenario=sample_scenario,
            persona=sample_persona,
            evaluation=sample_evaluation,
        )


def test_delete_session(history_service, sample_session, sample_scenario, sample_persona, sample_evaluation, sample_feedback):
    """Verify deleting a session removes it and cascades properly."""
    history_service.save_completed_session(
        session=sample_session,
        scenario=sample_scenario,
        persona=sample_persona,
        evaluation=sample_evaluation,
        feedback=sample_feedback,
    )
    assert history_service.count_sessions() == 1

    deleted = history_service.delete_session(sample_session.session_id)
    assert deleted is True
    assert history_service.count_sessions() == 0
    assert history_service.get_session(sample_session.session_id) is None


# --- 3. Transcript Filtering & Privacy Tests ---

def test_transcript_preservation_and_system_prompt_exclusion(history_service, sample_session, sample_scenario, sample_persona, sample_evaluation, sample_feedback):
    """
    Verify all 5 messages are stored with correct roles and timestamps,
    but user_facing_messages() strictly excludes the internal system prompt.
    """
    history_service.save_completed_session(
        session=sample_session,
        scenario=sample_scenario,
        persona=sample_persona,
        evaluation=sample_evaluation,
        feedback=sample_feedback,
    )
    loaded = history_service.get_session(sample_session.session_id)
    assert loaded is not None

    # Total messages in storage = 5 (1 system + 2 assistant + 2 user)
    assert len(loaded.messages) == 5

    # User facing messages = 4 (system prompt omitted)
    user_facing = loaded.user_facing_messages()
    assert len(user_facing) == 4
    for m in user_facing:
        assert m.role in ("user", "assistant")
        assert "Internal system prompt" not in m.content

    # Specific subsets
    assert len(loaded.user_messages()) == 2
    assert len(loaded.persona_messages()) == 2


# --- 4. Filtering Tests ---

def test_list_sessions_filtering(history_service, sample_scenario, sample_persona, sample_evaluation, sample_feedback):
    """Test filtering by mode, difficulty, score range, and scenario."""
    # Create session 1: Technical, Intermediate, Score 80.2
    s1 = PracticeSession(
        session_id="sess-1",
        mode="Technical Interview",
        difficulty="Intermediate",
        turn_number=3,
        status="completed",
    )
    eval1 = EvaluationResult(
        session_id="sess-1",
        mode="Technical Interview",
        difficulty="Intermediate",
        overall_score=80.2,
    )
    history_service.save_completed_session(s1, sample_scenario, sample_persona, eval1)

    hr_scenario = Scenario(
        id="hr_behavioral",
        name="Behavioral Intro",
        mode="HR Interview",
        description="Introduction and behavioral questions.",
        difficulty="Beginner",
    )
    hr_persona = Persona(
        id="hr_recruiter",
        name="Jordan",
        role="HR Lead",
        personality="Supportive, professional",
        background="Experienced HR leader",
        objective="Assess cultural alignment",
        knowledge_level="Generalist",
        communication_style="Conversational",
        difficulty="Beginner",
    )
    s2 = PracticeSession(
        session_id="sess-2",
        mode="HR Interview",
        difficulty="Beginner",
        turn_number=2,
        status="completed",
    )
    eval2 = EvaluationResult(
        session_id="sess-2",
        mode="HR Interview",
        difficulty="Beginner",
        overall_score=65.0,
    )
    history_service.save_completed_session(s2, hr_scenario, hr_persona, eval2)

    # Filter by mode
    tech_list = history_service.list_sessions(mode="Technical Interview")
    assert len(tech_list) == 1
    assert tech_list[0].session_id == "sess-1"

    hr_list = history_service.list_sessions(mode="HR Interview")
    assert len(hr_list) == 1
    assert hr_list[0].session_id == "sess-2"

    # Filter by difficulty
    beg_list = history_service.list_sessions(difficulty="Beginner")
    assert len(beg_list) == 1
    assert beg_list[0].session_id == "sess-2"

    # Filter by score
    high_score = history_service.list_sessions(min_score=75.0)
    assert len(high_score) == 1
    assert high_score[0].session_id == "sess-1"

    # Filter by scenario_id
    scen_list = history_service.list_sessions(scenario_id="tech_sys_design")
    assert len(scen_list) == 1
    assert scen_list[0].session_id == "sess-1"

    # Combined filter yielding empty
    empty_list = history_service.list_sessions(mode="HR Interview", min_score=90.0)
    assert len(empty_list) == 0


# --- 5. Session Summary Helper ---

def test_prepare_session_summary(history_service, sample_session, sample_scenario, sample_persona, sample_evaluation, sample_feedback):
    """Test generating UI-friendly session summary dictionary."""
    saved = history_service.save_completed_session(
        session=sample_session,
        scenario=sample_scenario,
        persona=sample_persona,
        evaluation=sample_evaluation,
        feedback=sample_feedback,
    )
    summary = history_service.prepare_session_summary(saved)
    assert summary["session_id"] == sample_session.session_id
    assert summary["mode"] == "Technical Interview"
    assert summary["score"] == 80.2
    assert summary["turns"] == 3
    assert summary["message_count"] == 4
    assert summary["strengths_count"] == 1
    assert summary["improvements_count"] == 1


# --- 6. Edge Cases ---

def test_nonexistent_session(history_service):
    """Verify querying an unknown session ID returns None without error."""
    assert history_service.get_session("non-existent-id") is None
    assert history_service.delete_session("non-existent-id") is False


def test_malformed_json_fallback(repository):
    """Verify repository survives if evaluation_json or feedback_json is corrupted in DB."""
    session = HistoricalSession(
        session_id="corrupt-json-1",
        created_at="2026-09-21T12:00:00",
        completed_at="2026-09-21T12:05:00",
        mode="HR Interview",
        scenario_id="test",
        scenario_name="Test",
        persona_id="test",
        persona_name="Test",
        difficulty="Beginner",
        turn_count=2,
        overall_score=70.0,
        raw_evaluation_json="INVALID_JSON{{{{",
        raw_feedback_json="INVALID_JSON{{{{",
    )
    repository.save_session(session)
    loaded = repository.get_session("corrupt-json-1")
    assert loaded is not None
    assert loaded.session_id == "corrupt-json-1"
    # Should fall back to None for parsed evaluation and feedback
    assert loaded.evaluation is None
    assert loaded.feedback is None


def test_long_transcript_preservation(history_service, sample_scenario, sample_persona):
    """Verify that a session with a long transcript (e.g. 50 turns) persists and retrieves accurately."""
    long_session = PracticeSession(
        session_id="long-transcript-sess",
        mode="Technical Interview",
        difficulty="Advanced",
        turn_number=25,
        status="completed",
    )
    long_messages = []
    for i in range(50):
        role = "assistant" if i % 2 == 0 else "user"
        content = f"Turn {i} content: testing deep conversation persistence with realistic payload."
        long_messages.append(ConversationMessage(role=role, content=content))
    long_session.conversation_history = long_messages

    eval_result = EvaluationResult(
        session_id="long-transcript-sess",
        mode="Technical Interview",
        difficulty="Advanced",
        overall_score=88.5,
    )

    history_service.save_completed_session(
        session=long_session,
        scenario=sample_scenario,
        persona=sample_persona,
        evaluation=eval_result,
    )

    loaded = history_service.get_session("long-transcript-sess")
    assert loaded is not None
    assert len(loaded.messages) == 50
    # Verify strict turn order preservation
    for i in range(50):
        assert loaded.messages[i].turn_order == i
        expected_role = "assistant" if i % 2 == 0 else "user"
        assert loaded.messages[i].role == expected_role


def test_date_range_filtering(history_service, sample_scenario, sample_persona):
    """Verify filtering sessions by start_date and end_date ranges."""
    s1 = PracticeSession(
        session_id="date-1",
        mode="Technical Interview",
        difficulty="Intermediate",
        turn_number=2,
        started_at="2026-08-01T10:00:00",
        ended_at="2026-08-01T10:10:00",
        status="completed",
    )
    s2 = PracticeSession(
        session_id="date-2",
        mode="Technical Interview",
        difficulty="Intermediate",
        turn_number=2,
        started_at="2026-09-01T10:00:00",
        ended_at="2026-09-01T10:10:00",
        status="completed",
    )
    eval_res = EvaluationResult(session_id="test", mode="Technical Interview", difficulty="Intermediate", overall_score=75.0)

    history_service.save_completed_session(s1, sample_scenario, sample_persona, eval_res)
    history_service.save_completed_session(s2, sample_scenario, sample_persona, eval_res)

    # Search August only
    aug_list = history_service.list_sessions(start_date="2026-08-01T00:00:00", end_date="2026-08-31T23:59:59")
    assert len(aug_list) == 1
    assert aug_list[0].session_id == "date-1"

    # Search September only
    sep_list = history_service.list_sessions(start_date="2026-09-01T00:00:00")
    assert len(sep_list) == 1
    assert sep_list[0].session_id == "date-2"


def test_no_score_recalculation_guarantee(history_service, sample_session, sample_scenario, sample_persona):
    """
    Verify historical records preserve their recorded score exactly as saved,
    and are not recalculated upon retrieval.
    """
    eval_result = EvaluationResult(
        session_id=sample_session.session_id,
        mode="Technical Interview",
        difficulty="Intermediate",
        overall_score=73.4,
        max_score=100.0,
        dimensions=[ScoreDimension(name="Topic Coverage", score=73.4)],
    )
    history_service.save_completed_session(
        session=sample_session,
        scenario=sample_scenario,
        persona=sample_persona,
        evaluation=eval_result,
    )

    loaded = history_service.get_session(sample_session.session_id)
    assert loaded is not None
    assert loaded.overall_score == 73.4
    assert loaded.evaluation is not None
    assert loaded.evaluation.overall_score == 73.4

