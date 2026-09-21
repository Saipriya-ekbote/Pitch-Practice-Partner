"""
Service Layer for Session History in Pitch Practice Partner.
Handles application-level validation, duration calculation, idempotency (duplicate prevention),
and conversion from runtime domain models to persistent historical records.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from src.scenarios.scenario_models import Scenario, Persona
from src.conversation.conversation_models import PracticeSession, SessionStatus
from src.evaluation.evaluation_models import EvaluationResult
from src.feedback.feedback_models import FeedbackResult
from src.history.history_models import (
    HistoricalSession,
    HistoricalMessage,
    HistoricalDimensionScore,
)
from src.history.history_repository import HistoryRepository


def calculate_session_duration(started_at: str, ended_at: Optional[str]) -> Optional[float]:
    """Calculate session duration in seconds between start and end timestamps."""
    if not started_at:
        return None
    try:
        t_start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        if ended_at:
            t_end = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
        else:
            t_end = datetime.now(timezone.utc)
        duration = (t_end - t_start).total_seconds()
        return max(0.0, duration)
    except Exception:
        return None


class HistoryService:
    """
    High-level service managing historical session persistence and retrieval.
    Enforces business rules such as completion requirements and duplicate prevention.
    """

    def __init__(self, repository: Optional[HistoryRepository] = None, db_path: Optional[str] = None):
        """Initialize with an existing repository or instantiate one at db_path."""
        if repository is not None:
            self.repository = repository
        else:
            self.repository = HistoryRepository(db_path=db_path)

    def save_completed_session(
        self,
        session: PracticeSession,
        scenario: Optional[Scenario] = None,
        persona: Optional[Persona] = None,
        evaluation: Optional[EvaluationResult] = None,
        feedback: Optional[FeedbackResult] = None,
        force_update: bool = False,
    ) -> HistoricalSession:
        """
        Validate and save a completed practice session to permanent history.
        
        Guarantees:
        - Only completed sessions with evaluation are persisted.
        - Prevents duplicate inserts for the same session_id (idempotent).
        - Preserves conversation transcript with role, content, order, and timestamps.
        - Preserves Phase 5 scores and Phase 6 feedback intact.
        """
        # Completion validation
        if not session.is_completed() and session.turn_number == 0:
            raise ValueError("Cannot save an unstarted or empty session to history.")

        # Check existing record for duplicate prevention
        existing = self.repository.get_session(session.session_id)
        if existing and not force_update:
            return existing

        completed_at = session.ended_at or datetime.now(timezone.utc).isoformat()
        duration_sec = calculate_session_duration(session.started_at, completed_at)

        # Convert transcript messages
        historical_messages: List[HistoricalMessage] = []
        for idx, msg in enumerate(session.conversation_history):
            historical_messages.append(
                HistoricalMessage(
                    role=msg.role,
                    content=msg.content,
                    turn_order=idx,
                    timestamp=msg.timestamp,
                )
            )

        # Convert evaluation dimensions
        historical_dimensions: List[HistoricalDimensionScore] = []
        overall_score = 0.0
        max_score = 100.0
        if evaluation:
            overall_score = evaluation.overall_score
            max_score = evaluation.max_score
            for dim in evaluation.dimensions:
                historical_dimensions.append(
                    HistoricalDimensionScore(
                        name=dim.name,
                        score=dim.score if dim.is_evaluated() else None,
                        max_score=dim.max_score,
                        weight=dim.weight,
                        status=dim.status,
                        evidence=list(dim.evidence),
                        rationale=dim.rationale,
                    )
                )

        scen_id = getattr(scenario, "id", getattr(scenario, "scenario_id", session.scenario_id)) if scenario else session.scenario_id
        scen_name = scenario.name if scenario else "Practice Scenario"
        pers_id = getattr(persona, "id", getattr(persona, "persona_id", session.persona_id)) if persona else session.persona_id
        pers_name = persona.name if persona else "Interviewer"
        mode_val = scenario.mode if scenario else session.mode

        historical_session = HistoricalSession(
            session_id=session.session_id,
            created_at=session.started_at,
            completed_at=completed_at,
            mode=mode_val,
            scenario_id=scen_id,
            scenario_name=scen_name,
            persona_id=pers_id,
            persona_name=pers_name,
            difficulty=session.difficulty,
            turn_count=session.turn_number,
            overall_score=overall_score,
            max_score=max_score,
            duration_seconds=duration_sec,
            evaluation_status="completed",
            messages=historical_messages,
            dimensions=historical_dimensions,
            evaluation=evaluation,
            feedback=feedback,
        )

        saved = self.repository.save_session(historical_session)
        if not saved:
            raise RuntimeError(f"Failed to persist historical session '{session.session_id}'.")

        return historical_session

    def get_session(self, session_id: str) -> Optional[HistoricalSession]:
        """Fetch a historical session by ID."""
        return self.repository.get_session(session_id)

    def list_sessions(
        self,
        mode: Optional[str] = None,
        difficulty: Optional[str] = None,
        scenario_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        order_by: str = "completed_at DESC",
    ) -> List[HistoricalSession]:
        """List sessions with optional filters."""
        return self.repository.list_sessions(
            mode=mode,
            difficulty=difficulty,
            scenario_id=scenario_id,
            start_date=start_date,
            end_date=end_date,
            min_score=min_score,
            max_score=max_score,
            order_by=order_by,
        )

    def delete_session(self, session_id: str) -> bool:
        """Permanently delete a session by ID."""
        return self.repository.delete_session(session_id)

    def count_sessions(
        self,
        mode: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> int:
        """Count total sessions matching mode or difficulty."""
        return self.repository.count_sessions(mode=mode, difficulty=difficulty)

    def clear_all(self) -> int:
        """Clear all historical sessions."""
        return self.repository.clear_all_sessions()

    def prepare_session_summary(self, session: HistoricalSession) -> Dict[str, Any]:
        """Generate a concise summary dict for UI display or reporting."""
        return {
            "session_id": session.session_id,
            "date": session.formatted_date,
            "mode": session.mode,
            "scenario": session.scenario_name,
            "persona": session.persona_name,
            "difficulty": session.difficulty,
            "turns": session.turn_count,
            "duration": session.formatted_duration,
            "score": round(session.overall_score, 1),
            "max_score": session.max_score,
            "message_count": len(session.user_facing_messages()),
            "strengths_count": len(session.feedback.strengths) if session.feedback else len(session.evaluation.strengths if session.evaluation else []),
            "improvements_count": len(session.feedback.improvements) if session.feedback else len(session.evaluation.improvement_areas if session.evaluation else []),
        }
