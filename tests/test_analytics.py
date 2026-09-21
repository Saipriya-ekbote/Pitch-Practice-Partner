"""
Unit tests for Phase 7: Analytics and Longitudinal Performance Tracking.
Covers summary statistics, chronological progress, mode breakdowns,
dimension averages, recurring patterns, two-session comparisons, determinism,
and edge cases.
"""

import os
import pytest
import tempfile
from datetime import datetime, timezone, timedelta

from src.scenarios.scenario_models import Scenario, Persona
from src.conversation.conversation_models import PracticeSession, ConversationMessage
from src.evaluation.evaluation_models import EvaluationResult, ScoreDimension
from src.feedback.feedback_models import (
    FeedbackResult,
    FeedbackItem,
    StrengthFeedbackItem,
    ImprovementFeedbackItem,
    PracticeAction,
)
from src.history import (
    HistoryRepository,
    HistoryService,
    AnalyticsService,
    compare_sessions,
)


@pytest.fixture
def temp_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def history_service(temp_db_path):
    repo = HistoryRepository(db_path=temp_db_path)
    return HistoryService(repository=repo)


@pytest.fixture
def analytics_service(history_service):
    return AnalyticsService(history_service=history_service)


def create_mock_session(
    service: HistoryService,
    session_id: str,
    completed_at: str,
    mode: str,
    difficulty: str,
    overall_score: float,
    turn_count: int = 3,
    strengths=None,
    improvements=None,
    dimensions=None,
):
    scenario = Scenario(
        id=f"scen_{session_id}",
        name=f"Scenario {session_id}",
        mode=mode,
        description=f"Description for {session_id}",
        difficulty=difficulty,
    )
    persona = Persona(
        id=f"pers_{session_id}",
        name="Alex",
        role="Evaluator",
        personality="Analytical, observant",
        background="Experienced professional interviewer",
        objective="Assess candidate communication skills",
        knowledge_level="Expert",
        communication_style="Professional",
        difficulty=difficulty,
    )
    session = PracticeSession(
        session_id=session_id,
        mode=mode,
        difficulty=difficulty,
        turn_number=turn_count,
        started_at=(datetime.fromisoformat(completed_at) - timedelta(minutes=5)).isoformat(),
        ended_at=completed_at,
        status="completed",
    )
    # Add dummy messages
    session.conversation_history = [
        ConversationMessage(role="assistant", content="Hello candidate."),
        ConversationMessage(role="user", content="Hello interviewer."),
    ]

    dims = dimensions or [
        ScoreDimension(name="Question Handling", score=overall_score),
        ScoreDimension(name="Fluency", score=overall_score - 2.0),
    ]

    eval_result = EvaluationResult(
        session_id=session_id,
        mode=mode,
        difficulty=difficulty,
        overall_score=overall_score,
        dimensions=dims,
        strengths=[s.title for s in (strengths or [])],
        improvement_areas=[i.title for i in (improvements or [])],
    )

    feedback_result = FeedbackResult(
        session_id=session_id,
        mode=mode,
        difficulty=difficulty,
        overall_summary=f"Summary for {session_id}",
        strengths=strengths or [],
        improvements=improvements or [],
    )

    return service.save_completed_session(
        session=session,
        scenario=scenario,
        persona=persona,
        evaluation=eval_result,
        feedback=feedback_result,
    )


# --- 1. Empty State Tests ---

def test_empty_analytics(analytics_service):
    """Verify analytics on empty database returns zeroed metrics without crashing."""
    summary = analytics_service.get_overall_summary()
    assert summary["total_sessions"] == 0
    assert summary["average_score"] == 0.0
    assert summary["has_sufficient_data"] is False

    prog = analytics_service.get_chronological_progress()
    assert len(prog) == 0

    modes = analytics_service.get_mode_breakdown()
    assert len(modes) == 0

    dims = analytics_service.get_dimension_averages()
    assert len(dims) == 0

    improvements = analytics_service.get_recurring_improvements()
    assert len(improvements) == 0


# --- 2. Summary Statistics Tests ---

def test_overall_summary_calculation(history_service, analytics_service):
    """Verify total sessions, score averages, max/min, turns, and duration."""
    create_mock_session(
        history_service,
        session_id="s1",
        completed_at="2026-09-01T10:00:00",
        mode="HR Interview",
        difficulty="Beginner",
        overall_score=60.0,
        turn_count=3,
    )
    create_mock_session(
        history_service,
        session_id="s2",
        completed_at="2026-09-02T10:00:00",
        mode="Technical Interview",
        difficulty="Intermediate",
        overall_score=80.0,
        turn_count=5,
    )

    summary = analytics_service.get_overall_summary()
    assert summary["total_sessions"] == 2
    assert summary["average_score"] == 70.0
    assert summary["highest_recorded_score"] == 80.0
    assert summary["lowest_recorded_score"] == 60.0
    assert summary["average_turns"] == 4.0
    assert summary["total_turns"] == 8
    assert summary["has_sufficient_data"] is True


# --- 3. Chronological Progress Tests ---

def test_chronological_progress_ordering(history_service, analytics_service):
    """Verify sessions are strictly chronologically ordered by completed_at."""
    # Insert in non-chronological order
    create_mock_session(
        history_service,
        session_id="s2",
        completed_at="2026-09-10T12:00:00",
        mode="Client Pitch",
        difficulty="Intermediate",
        overall_score=75.0,
    )
    create_mock_session(
        history_service,
        session_id="s1",
        completed_at="2026-09-05T12:00:00",
        mode="HR Interview",
        difficulty="Beginner",
        overall_score=68.0,
    )
    create_mock_session(
        history_service,
        session_id="s3",
        completed_at="2026-09-15T12:00:00",
        mode="Technical Interview",
        difficulty="Advanced",
        overall_score=84.0,
    )

    progress = analytics_service.get_chronological_progress()
    assert len(progress) == 3
    assert progress[0]["session_id"] == "s1"
    assert progress[0]["score"] == 68.0
    assert progress[1]["session_id"] == "s2"
    assert progress[1]["score"] == 75.0
    assert progress[2]["session_id"] == "s3"
    assert progress[2]["score"] == 84.0


# --- 4. Mode and Difficulty Breakdowns ---

def test_mode_and_difficulty_breakdowns(history_service, analytics_service):
    """Verify group statistics by practice mode and difficulty level."""
    create_mock_session(
        history_service,
        session_id="m1",
        completed_at="2026-09-01T10:00:00",
        mode="HR Interview",
        difficulty="Beginner",
        overall_score=70.0,
    )
    create_mock_session(
        history_service,
        session_id="m2",
        completed_at="2026-09-02T10:00:00",
        mode="HR Interview",
        difficulty="Intermediate",
        overall_score=80.0,
    )
    create_mock_session(
        history_service,
        session_id="m3",
        completed_at="2026-09-03T10:00:00",
        mode="Client Pitch",
        difficulty="Advanced",
        overall_score=90.0,
    )

    # Mode Breakdown
    mode_stats = analytics_service.get_mode_breakdown()
    assert len(mode_stats) == 2
    pitch_stat = next(m for m in mode_stats if m["mode"] == "Client Pitch")
    assert pitch_stat["session_count"] == 1
    assert pitch_stat["average_score"] == 90.0

    hr_stat = next(m for m in mode_stats if m["mode"] == "HR Interview")
    assert hr_stat["session_count"] == 2
    assert hr_stat["average_score"] == 75.0
    assert hr_stat["lowest_score"] == 70.0
    assert hr_stat["highest_score"] == 80.0

    # Difficulty Breakdown
    diff_stats = analytics_service.get_difficulty_breakdown()
    diff_names = [d["difficulty"] for d in diff_stats]
    assert "Beginner" in diff_names
    assert "Intermediate" in diff_names
    assert "Advanced" in diff_names


# --- 5. Dimension Analytics ---

def test_dimension_averages(history_service, analytics_service):
    """Verify dimension averages aggregate correctly across sessions."""
    dims_1 = [
        ScoreDimension(name="Question Handling", score=80.0),
        ScoreDimension(name="Conciseness", score=70.0),
    ]
    dims_2 = [
        ScoreDimension(name="Question Handling", score=90.0),
        ScoreDimension(name="Conciseness", score=80.0),
        ScoreDimension(name="Architecture Depth", score=85.0),
    ]
    create_mock_session(
        history_service,
        session_id="d1",
        completed_at="2026-09-01T10:00:00",
        mode="Technical Interview",
        difficulty="Intermediate",
        overall_score=75.0,
        dimensions=dims_1,
    )
    create_mock_session(
        history_service,
        session_id="d2",
        completed_at="2026-09-02T10:00:00",
        mode="Technical Interview",
        difficulty="Intermediate",
        overall_score=85.0,
        dimensions=dims_2,
    )

    dim_averages = analytics_service.get_dimension_averages()
    dim_map = {d["dimension"]: d for d in dim_averages}

    assert dim_map["Question Handling"]["average_score"] == 85.0
    assert dim_map["Question Handling"]["evaluations_count"] == 2
    assert dim_map["Conciseness"]["average_score"] == 75.0
    assert dim_map["Architecture Depth"]["average_score"] == 85.0
    assert dim_map["Architecture Depth"]["evaluations_count"] == 1


# --- 6. Recurring Patterns Tests ---

def test_recurring_improvements_and_strengths(history_service, analytics_service):
    """Verify frequent improvement themes and strengths are counted across sessions."""
    imp_a = ImprovementFeedbackItem(
        title="Follow-up Probing",
        what="Missed sub-question.",
        why="Lacks completeness.",
        evidence="Quote 1",
        impact="Interviewer repeats question.",
        action="Answer sub-parts sequentially.",
    )
    imp_b = ImprovementFeedbackItem(
        title="Filler Word Frequency",
        what="Used 8 filler words.",
        why="Distracts from message.",
        evidence="Quote 2",
        impact="Lowers perceived fluency.",
        action="Pause deliberately.",
    )
    str_a = StrengthFeedbackItem(
        title="Clear Architecture Explanations",
        what="Articulated database scaling clearly.",
        evidence="Quote 3",
        impact="Establishes credibility.",
    )

    # Session 1: Follow-up Probing + Clear Architecture
    create_mock_session(
        history_service,
        session_id="p1",
        completed_at="2026-09-01T10:00:00",
        mode="Technical Interview",
        difficulty="Intermediate",
        overall_score=72.0,
        strengths=[str_a],
        improvements=[imp_a],
    )
    # Session 2: Follow-up Probing + Filler Words + Clear Architecture
    create_mock_session(
        history_service,
        session_id="p2",
        completed_at="2026-09-02T10:00:00",
        mode="Technical Interview",
        difficulty="Intermediate",
        overall_score=76.0,
        strengths=[str_a],
        improvements=[imp_a, imp_b],
    )

    # Check recurring improvements
    recurring_imps = analytics_service.get_recurring_improvements()
    assert len(recurring_imps) == 2
    assert recurring_imps[0]["theme"] == "Follow-up Probing"
    assert recurring_imps[0]["occurrences"] == 2
    assert recurring_imps[1]["theme"] == "Filler Word Frequency"
    assert recurring_imps[1]["occurrences"] == 1

    # Check recurring strengths
    recurring_strs = analytics_service.get_recurring_strengths()
    assert len(recurring_strs) == 1
    assert recurring_strs[0]["strength"] == "Clear Architecture Explanations"
    assert recurring_strs[0]["occurrences"] == 2


# --- 7. Session Comparison Tests ---

def test_compare_sessions(history_service):
    """Verify neutral two-session comparison logic and delta calculation."""
    s1 = create_mock_session(
        history_service,
        session_id="comp_1",
        completed_at="2026-09-01T10:00:00",
        mode="HR Interview",
        difficulty="Intermediate",
        overall_score=68.0,
        turn_count=3,
        dimensions=[
            ScoreDimension(name="Question Handling", score=70.0),
            ScoreDimension(name="Communication Fluency", score=66.0),
        ],
        strengths=[StrengthFeedbackItem(title="Direct Answers", what="Good", evidence="ev", impact="imp")],
        improvements=[ImprovementFeedbackItem(title="Elaborate Impact", what="Brief", why="Why", evidence="ev", impact="imp", action="act")],
    )
    s2 = create_mock_session(
        history_service,
        session_id="comp_2",
        completed_at="2026-09-05T10:00:00",
        mode="HR Interview",
        difficulty="Intermediate",
        overall_score=77.0,
        turn_count=4,
        dimensions=[
            ScoreDimension(name="Question Handling", score=78.0),
            ScoreDimension(name="Communication Fluency", score=76.0),
        ],
        strengths=[
            StrengthFeedbackItem(title="Direct Answers", what="Good", evidence="ev", impact="imp"),
            StrengthFeedbackItem(title="Structured Delivery", what="Good", evidence="ev", impact="imp"),
        ],
        improvements=[ImprovementFeedbackItem(title="Pacing", what="Fast", why="Why", evidence="ev", impact="imp", action="act")],
    )

    comparison = compare_sessions(s1, s2)
    assert comparison["overall_score_difference"] == 9.0
    assert "Recorded score difference: +9.0 points." in comparison["overall_score_description"]
    assert comparison["turn_difference"] == 1

    # Check dimensional comparisons
    dim_comps = {d["dimension"]: d for d in comparison["dimension_comparisons"]}
    assert dim_comps["Question Handling"]["difference"] == 8.0
    assert dim_comps["Communication Fluency"]["difference"] == 10.0

    # Common and distinct strengths
    assert "Direct Answers" in comparison["common_strengths"]
    assert "Structured Delivery" in comparison["distinct_b_strengths"]

    # Common and distinct improvements
    assert "Elaborate Impact" in comparison["distinct_a_improvements"]
    assert "Pacing" in comparison["distinct_b_improvements"]


# --- 8. Determinism Tests ---

def test_analytics_determinism(history_service, analytics_service):
    """Verify that identical input data produces identical analytics results across multiple calls."""
    create_mock_session(
        history_service,
        session_id="det_1",
        completed_at="2026-09-01T10:00:00",
        mode="Technical Interview",
        difficulty="Intermediate",
        overall_score=75.0,
    )
    create_mock_session(
        history_service,
        session_id="det_2",
        completed_at="2026-09-02T10:00:00",
        mode="Technical Interview",
        difficulty="Advanced",
        overall_score=82.0,
    )

    summary_1 = analytics_service.get_overall_summary()
    summary_2 = analytics_service.get_overall_summary()
    assert summary_1 == summary_2

    prog_1 = analytics_service.get_chronological_progress()
    prog_2 = analytics_service.get_chronological_progress()
    assert prog_1 == prog_2

    modes_1 = analytics_service.get_mode_breakdown()
    modes_2 = analytics_service.get_mode_breakdown()
    assert modes_1 == modes_2


def test_single_session_analytics(history_service, analytics_service):
    """Verify single session provides valid metrics without errors."""
    create_mock_session(
        history_service,
        session_id="single_1",
        completed_at="2026-09-01T10:00:00",
        mode="Group Discussion",
        difficulty="Intermediate",
        overall_score=78.0,
        turn_count=4,
    )
    summary = analytics_service.get_overall_summary()
    assert summary["total_sessions"] == 1
    assert summary["average_score"] == 78.0
    assert summary["highest_recorded_score"] == 78.0
    assert summary["lowest_recorded_score"] == 78.0

    prog = analytics_service.get_chronological_progress()
    assert len(prog) == 1
    assert prog[0]["score"] == 78.0


def test_compare_sessions_with_missing_dimension(history_service):
    """Verify comparing two sessions where a dimension is evaluated in only one of them."""
    s1 = create_mock_session(
        history_service,
        session_id="diff_dim_1",
        completed_at="2026-09-01T10:00:00",
        mode="HR Interview",
        difficulty="Beginner",
        overall_score=70.0,
        dimensions=[ScoreDimension(name="STAR Completeness", score=75.0)],
    )
    s2 = create_mock_session(
        history_service,
        session_id="diff_dim_2",
        completed_at="2026-09-02T10:00:00",
        mode="Technical Interview",
        difficulty="Advanced",
        overall_score=85.0,
        dimensions=[ScoreDimension(name="System Scalability", score=90.0)],
    )

    comparison = compare_sessions(s1, s2)
    dim_map = {d["dimension"]: d for d in comparison["dimension_comparisons"]}
    assert "STAR Completeness" in dim_map
    assert dim_map["STAR Completeness"]["score_a"] == 75.0
    assert dim_map["STAR Completeness"]["score_b"] is None
    assert dim_map["STAR Completeness"]["difference_display"] == "N/A"

    assert "System Scalability" in dim_map
    assert dim_map["System Scalability"]["score_a"] is None
    assert dim_map["System Scalability"]["score_b"] == 90.0
    assert dim_map["System Scalability"]["difference_display"] == "N/A"


def test_analytics_date_range_filtering(history_service, analytics_service):
    """
    Verify date-range filtering on analytics:
    - Start date can be selected
    - End date can be selected
    - Results/analytics change according to the selected date range
    - Empty date ranges are handled safely
    - No stored records outside the selected range are included
    - Existing mode/difficulty filters continue working
    """
    # Create session in August
    create_mock_session(
        history_service,
        session_id="aug_sess",
        completed_at="2026-08-15T14:30:00",
        mode="HR Interview",
        difficulty="Beginner",
        overall_score=62.0,
    )
    # Create session in September (HR)
    create_mock_session(
        history_service,
        session_id="sep_sess_1",
        completed_at="2026-09-10T10:00:00",
        mode="HR Interview",
        difficulty="Intermediate",
        overall_score=78.0,
    )
    # Create session in September (Technical)
    create_mock_session(
        history_service,
        session_id="sep_sess_2",
        completed_at="2026-09-20T16:00:00",
        mode="Technical Interview",
        difficulty="Advanced",
        overall_score=88.0,
    )

    # 1. Unfiltered: all 3 sessions
    all_sess = analytics_service.get_sessions()
    assert len(all_sess) == 3
    summary_all = analytics_service.get_overall_summary(all_sess)
    assert summary_all["total_sessions"] == 3

    # 2. Filter by August range only
    aug_sess = analytics_service.get_sessions(
        start_date="2026-08-01T00:00:00",
        end_date="2026-08-31T23:59:59",
    )
    assert len(aug_sess) == 1
    assert aug_sess[0].session_id == "aug_sess"
    summary_aug = analytics_service.get_overall_summary(aug_sess)
    assert summary_aug["total_sessions"] == 1
    assert summary_aug["average_score"] == 62.0

    # 3. Filter by September range only
    sep_sess = analytics_service.get_sessions(
        start_date="2026-09-01T00:00:00",
        end_date="2026-09-30T23:59:59",
    )
    assert len(sep_sess) == 2
    summary_sep = analytics_service.get_overall_summary(sep_sess)
    assert summary_sep["total_sessions"] == 2
    assert summary_sep["average_score"] == 83.0  # (78 + 88)/2
    assert summary_sep["lowest_recorded_score"] == 78.0
    assert summary_sep["highest_recorded_score"] == 88.0

    # 4. Filter with combined Date Range + Mode filter
    sep_hr_sess = analytics_service.get_sessions(
        mode="HR Interview",
        start_date="2026-09-01T00:00:00",
        end_date="2026-09-30T23:59:59",
    )
    assert len(sep_hr_sess) == 1
    assert sep_hr_sess[0].session_id == "sep_sess_1"

    # 5. Out of range date yields empty result safely
    empty_sess = analytics_service.get_sessions(
        start_date="2026-10-01T00:00:00",
        end_date="2026-10-31T23:59:59",
    )
    assert len(empty_sess) == 0
    empty_summary = analytics_service.get_overall_summary(empty_sess)
    assert empty_summary["total_sessions"] == 0
    assert empty_summary["has_sufficient_data"] is False


