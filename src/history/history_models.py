"""
Historical Session and Message Data Models for Pitch Practice Partner.
Preserves completed practice sessions, conversation transcripts, evaluation scores,
and explainable feedback records for longitudinal history and analytics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import List, Dict, Any, Optional

from src.evaluation.evaluation_models import (
    EvaluationResult,
    ScoreDimension,
    ModeEvaluation,
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
    EvidenceConfidence,
)


def evaluation_to_dict(eval_result: Optional[EvaluationResult]) -> Optional[Dict[str, Any]]:
    """Convert an EvaluationResult to dictionary safely."""
    if eval_result is None:
        return None
    return eval_result.to_dict()


def evaluation_from_dict(data: Optional[Dict[str, Any]]) -> Optional[EvaluationResult]:
    """Reconstruct an EvaluationResult from a dictionary representation."""
    if not data or not isinstance(data, dict):
        return None
    try:
        dimensions = []
        for dim_data in data.get("dimensions", []):
            score = dim_data.get("score")
            status = dim_data.get("status", DimensionStatus.EVALUATED.value)
            # If score is None or not evaluated, default to 0.0 with status
            dim_score = float(score) if score is not None else 0.0
            dimensions.append(
                ScoreDimension(
                    name=str(dim_data.get("name", "Unknown")),
                    score=dim_score,
                    max_score=float(dim_data.get("max_score", 100.0)),
                    weight=float(dim_data.get("weight", 1.0)),
                    status=str(status),
                    evidence=list(dim_data.get("evidence", [])),
                    rationale=str(dim_data.get("rationale", "")),
                )
            )

        mode_eval = None
        if data.get("mode_specific_evaluation"):
            me_data = data["mode_specific_evaluation"]
            me_dims = []
            for d in me_data.get("dimensions", []):
                score = d.get("score")
                me_dims.append(
                    ScoreDimension(
                        name=str(d.get("name", "")),
                        score=float(score) if score is not None else 0.0,
                        max_score=float(d.get("max_score", 100.0)),
                        weight=float(d.get("weight", 1.0)),
                        status=str(d.get("status", DimensionStatus.EVALUATED.value)),
                        evidence=list(d.get("evidence", [])),
                        rationale=str(d.get("rationale", "")),
                    )
                )
            mode_eval = ModeEvaluation(
                mode=str(me_data.get("mode", data.get("mode", ""))),
                dimensions=me_dims,
                mode_notes=list(me_data.get("mode_notes", [])),
            )

        return EvaluationResult(
            session_id=str(data.get("session_id", "")),
            mode=str(data.get("mode", "")),
            difficulty=str(data.get("difficulty", "Intermediate")),
            overall_score=float(data.get("overall_score", 0.0)),
            max_score=float(data.get("max_score", 100.0)),
            dimensions=dimensions,
            strengths=list(data.get("strengths", [])),
            improvement_areas=list(data.get("improvement_areas", [])),
            insufficient_evidence_dimensions=list(data.get("insufficient_evidence_dimensions", [])),
            mode_specific_evaluation=mode_eval,
        )
    except Exception:
        return None


def feedback_to_dict(feedback_result: Optional[FeedbackResult]) -> Optional[Dict[str, Any]]:
    """Convert a FeedbackResult to dictionary safely."""
    if feedback_result is None:
        return None
    return feedback_result.to_dict()


def feedback_from_dict(data: Optional[Dict[str, Any]]) -> Optional[FeedbackResult]:
    """Reconstruct a FeedbackResult from a dictionary representation."""
    if not data or not isinstance(data, dict):
        return None
    try:
        items = []
        for it in data.get("items", []):
            score = it.get("score")
            items.append(
                FeedbackItem(
                    dimension=str(it.get("dimension", "")),
                    status=str(it.get("status", "evaluated")),
                    what=str(it.get("what", "")),
                    why=str(it.get("why", "")),
                    evidence=str(it.get("evidence", "")),
                    impact=str(it.get("impact", "")),
                    action=str(it.get("action", "")),
                    score=float(score) if score is not None else None,
                    max_score=float(it.get("max_score", 100.0)),
                    evidence_type=str(it.get("evidence_type", EvidenceType.ANALYSIS_OBSERVATION.value)),
                    source_reference=str(it.get("source_reference", "")),
                    priority=str(it.get("priority", FeedbackPriority.MEDIUM.value)),
                    confidence=str(it.get("confidence", EvidenceConfidence.SUFFICIENT.value)),
                )
            )

        strengths = []
        for s in data.get("strengths", []):
            strengths.append(
                StrengthFeedbackItem(
                    title=str(s.get("title", "")),
                    what=str(s.get("what", "")),
                    evidence=str(s.get("evidence", "")),
                    impact=str(s.get("impact", "")),
                    evidence_type=str(s.get("evidence_type", EvidenceType.ANALYSIS_OBSERVATION.value)),
                    source_reference=str(s.get("source_reference", "")),
                )
            )

        improvements = []
        for imp in data.get("improvements", []):
            improvements.append(
                ImprovementFeedbackItem(
                    title=str(imp.get("title", "")),
                    what=str(imp.get("what", "")),
                    why=str(imp.get("why", "")),
                    evidence=str(imp.get("evidence", "")),
                    impact=str(imp.get("impact", "")),
                    action=str(imp.get("action", "")),
                    priority=str(imp.get("priority", FeedbackPriority.HIGH.value)),
                    evidence_type=str(imp.get("evidence_type", EvidenceType.ANALYSIS_OBSERVATION.value)),
                    source_reference=str(imp.get("source_reference", "")),
                )
            )

        priority_actions = []
        for pa in data.get("priority_actions", []):
            priority_actions.append(
                PracticeAction(
                    title=str(pa.get("title", "")),
                    action=str(pa.get("action", "")),
                    scenario_context=str(pa.get("scenario_context", "")),
                    priority=str(pa.get("priority", FeedbackPriority.HIGH.value)),
                )
            )

        return FeedbackResult(
            session_id=str(data.get("session_id", "")),
            mode=str(data.get("mode", "")),
            difficulty=str(data.get("difficulty", "Intermediate")),
            overall_summary=str(data.get("overall_summary", "")),
            items=items,
            strengths=strengths,
            improvements=improvements,
            priority_actions=priority_actions,
            insufficient_evidence_notes=list(data.get("insufficient_evidence_notes", [])),
        )
    except Exception:
        return None


@dataclass
class HistoricalMessage:
    """
    Stored message from a completed practice session.
    
    Attributes:
        role: Role of speaker ('system', 'assistant', 'user').
        content: Text content of the message.
        turn_order: 0-indexed position in the conversation.
        timestamp: ISO format timestamp string.
    """
    role: str
    content: str
    turn_order: int = 0
    timestamp: Optional[str] = None

    def is_user_facing(self) -> bool:
        """Return True if message should be shown in user transcript (exclude internal system prompts)."""
        return self.role in ("user", "assistant")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "turn_order": self.turn_order,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoricalMessage":
        return cls(
            role=str(data.get("role", "user")),
            content=str(data.get("content", "")),
            turn_order=int(data.get("turn_order", 0)),
            timestamp=data.get("timestamp"),
        )


@dataclass
class HistoricalDimensionScore:
    """
    Dimension score record persisted for fast aggregation and trend analysis.
    """
    name: str
    score: Optional[float] = None
    max_score: float = 100.0
    weight: float = 1.0
    status: str = "evaluated"
    evidence: List[str] = field(default_factory=list)
    rationale: str = ""

    def is_evaluated(self) -> bool:
        return self.status == "evaluated" and self.score is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 1) if self.score is not None else None,
            "max_score": self.max_score,
            "weight": self.weight,
            "status": self.status,
            "evidence": self.evidence,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoricalDimensionScore":
        score = data.get("score")
        return cls(
            name=str(data.get("name", "")),
            score=float(score) if score is not None else None,
            max_score=float(data.get("max_score", 100.0)),
            weight=float(data.get("weight", 1.0)),
            status=str(data.get("status", "evaluated")),
            evidence=list(data.get("evidence", [])),
            rationale=str(data.get("rationale", "")),
        )


@dataclass
class HistoricalSession:
    """
    Complete persistent historical record of a finished practice session.
    """
    session_id: str
    created_at: str
    completed_at: str
    mode: str
    scenario_id: str
    scenario_name: str
    persona_id: str
    persona_name: str
    difficulty: str
    turn_count: int
    overall_score: float
    max_score: float = 100.0
    duration_seconds: Optional[float] = None
    evaluation_status: str = "completed"
    messages: List[HistoricalMessage] = field(default_factory=list)
    dimensions: List[HistoricalDimensionScore] = field(default_factory=list)
    evaluation: Optional[EvaluationResult] = None
    feedback: Optional[FeedbackResult] = None
    raw_evaluation_json: Optional[str] = None
    raw_feedback_json: Optional[str] = None

    @property
    def formatted_duration(self) -> str:
        """Format duration into human-readable representation (e.g. '2m 14s' or '45s')."""
        if self.duration_seconds is None or self.duration_seconds < 0:
            return "N/A"
        secs = int(round(self.duration_seconds))
        minutes = secs // 60
        remaining_secs = secs % 60
        if minutes > 0:
            return f"{minutes}m {remaining_secs:02d}s"
        return f"{remaining_secs}s"

    @property
    def formatted_date(self) -> str:
        """Format completed_at timestamp into standard display string."""
        try:
            # Handle ISO format strings
            clean_ts = self.completed_at.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
            return dt.strftime("%b %d, %Y %H:%M")
        except Exception:
            return self.completed_at

    def user_facing_messages(self) -> List[HistoricalMessage]:
        """Return only messages intended for user review, strictly omitting system prompts."""
        return [m for m in self.messages if m.is_user_facing()]

    def user_messages(self) -> List[HistoricalMessage]:
        """Return candidate/user messages only."""
        return [m for m in self.messages if m.role == "user"]

    def persona_messages(self) -> List[HistoricalMessage]:
        """Return AI persona messages only."""
        return [m for m in self.messages if m.role == "assistant"]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize HistoricalSession to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "mode": self.mode,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "persona_id": self.persona_id,
            "persona_name": self.persona_name,
            "difficulty": self.difficulty,
            "turn_count": self.turn_count,
            "duration_seconds": self.duration_seconds,
            "overall_score": round(self.overall_score, 1),
            "max_score": self.max_score,
            "evaluation_status": self.evaluation_status,
            "messages": [m.to_dict() for m in self.messages],
            "dimensions": [d.to_dict() for d in self.dimensions],
            "evaluation": evaluation_to_dict(self.evaluation),
            "feedback": feedback_to_dict(self.feedback),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoricalSession":
        """Construct HistoricalSession from dictionary."""
        messages = [
            HistoricalMessage.from_dict(m) for m in data.get("messages", [])
        ]
        dimensions = [
            HistoricalDimensionScore.from_dict(d) for d in data.get("dimensions", [])
        ]
        eval_obj = None
        if data.get("evaluation"):
            eval_obj = evaluation_from_dict(data["evaluation"])
        feedback_obj = None
        if data.get("feedback"):
            feedback_obj = feedback_from_dict(data["feedback"])

        return cls(
            session_id=str(data.get("session_id", "")),
            created_at=str(data.get("created_at", "")),
            completed_at=str(data.get("completed_at", "")),
            mode=str(data.get("mode", "")),
            scenario_id=str(data.get("scenario_id", "")),
            scenario_name=str(data.get("scenario_name", "")),
            persona_id=str(data.get("persona_id", "")),
            persona_name=str(data.get("persona_name", "")),
            difficulty=str(data.get("difficulty", "Intermediate")),
            turn_count=int(data.get("turn_count", 0)),
            overall_score=float(data.get("overall_score", 0.0)),
            max_score=float(data.get("max_score", 100.0)),
            duration_seconds=data.get("duration_seconds"),
            evaluation_status=str(data.get("evaluation_status", "completed")),
            messages=messages,
            dimensions=dimensions,
            evaluation=eval_obj,
            feedback=feedback_obj,
        )
