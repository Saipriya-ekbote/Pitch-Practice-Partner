"""
Data models for Explainable Feedback Engine.
Implements the WHAT / WHY / EVIDENCE / IMPACT / ACTION framework.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class FeedbackPriority(str, Enum):
    """Priority level for feedback and improvement actions."""
    HIGH = "High Priority"
    MEDIUM = "Medium Priority"
    LOW = "Low Priority"


class EvidenceType(str, Enum):
    """Type of evidence backing a feedback observation."""
    TRANSCRIPT_EXCERPT = "Transcript excerpt"
    ANALYSIS_OBSERVATION = "Analysis observation"
    NONE = "None"


class EvidenceConfidence(str, Enum):
    """Confidence and sufficiency level of conversational evidence."""
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class FeedbackItem:
    """
    Core explainable feedback item connecting evaluation dimensions to concrete actions.
    
    Attributes:
        dimension: Name of the evaluation dimension (e.g., 'Question Handling', 'STAR Framework Completeness').
        status: Evaluation status ('evaluated', 'insufficient_evidence', 'not_applicable').
        what: Factual observation of what occurred in the conversation.
        why: Rationale explaining why this observation affected the score or assessment.
        evidence: Verifiable quote or structured analysis observation from the session.
        impact: Real-world significance in the selected scenario or domain.
        action: Concrete, actionable technique the user can apply in their next practice turn.
        score: Associated numerical score from Phase 5 (if evaluated).
        max_score: Maximum achievable score (standardized to 100.0).
        evidence_type: Classification of evidence ('Transcript excerpt', 'Analysis observation', 'None').
        source_reference: Pointer to conversation location (e.g., 'Turn 2', 'Linguistic analysis').
        priority: Urgency level ('High Priority', 'Medium Priority', 'Low Priority').
        confidence: Evidence sufficiency status ('sufficient', 'insufficient', 'not_applicable').
    """
    dimension: str
    status: str
    what: str
    why: str
    evidence: str
    impact: str
    action: str
    score: Optional[float] = None
    max_score: float = 100.0
    evidence_type: str = EvidenceType.ANALYSIS_OBSERVATION.value
    source_reference: str = ""
    priority: str = FeedbackPriority.MEDIUM.value
    confidence: str = EvidenceConfidence.SUFFICIENT.value

    def __post_init__(self) -> None:
        """Validate model integrity."""
        if not self.dimension:
            raise ValueError("FeedbackItem must specify a non-empty dimension name.")
        if not self.what:
            raise ValueError("FeedbackItem must contain a 'what' observation.")
        if not self.why:
            raise ValueError("FeedbackItem must contain a 'why' rationale.")
        if not self.impact:
            raise ValueError("FeedbackItem must contain an 'impact' explanation.")
        if not self.action:
            raise ValueError("FeedbackItem must contain an 'action' guideline.")
        if self.score is not None and (self.score < 0.0 or self.score > self.max_score):
            raise ValueError(f"Score {self.score} must be between 0.0 and {self.max_score}.")

    def is_evaluated(self) -> bool:
        """Return True if dimension has sufficient evidence and was scored."""
        return self.status == "evaluated" and self.score is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert FeedbackItem to structured dictionary."""
        return {
            "dimension": self.dimension,
            "status": self.status,
            "score": round(self.score, 1) if self.score is not None else None,
            "max_score": self.max_score,
            "what": self.what,
            "why": self.why,
            "evidence": self.evidence,
            "evidence_type": self.evidence_type,
            "source_reference": self.source_reference,
            "impact": self.impact,
            "action": self.action,
            "priority": self.priority,
            "confidence": self.confidence,
        }


@dataclass
class StrengthFeedbackItem:
    """
    Evidence-grounded positive feedback item.
    
    Attributes:
        title: Concise title for the strength (e.g., 'Fluent Delivery').
        what: Factual observation of candidate success.
        evidence: Direct transcript quote or factual metric supporting the observation.
        impact: Value this provides in the communication context.
        evidence_type: Classification of evidence ('Transcript excerpt', 'Analysis observation').
        source_reference: Source turn or signal reference.
    """
    title: str
    what: str
    evidence: str
    impact: str
    evidence_type: str = EvidenceType.ANALYSIS_OBSERVATION.value
    source_reference: str = ""

    def __post_init__(self) -> None:
        if not self.title or not self.what or not self.evidence or not self.impact:
            raise ValueError("StrengthFeedbackItem requires title, what, evidence, and impact.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert StrengthFeedbackItem to dictionary."""
        return {
            "title": self.title,
            "what": self.what,
            "evidence": self.evidence,
            "evidence_type": self.evidence_type,
            "source_reference": self.source_reference,
            "impact": self.impact,
        }


@dataclass
class ImprovementFeedbackItem:
    """
    Actionable improvement area grounded in real conversational gaps.
    
    Attributes:
        title: Concise title of the improvement area.
        what: Factual observation of the gap.
        why: Explanation of why this hindered communication or scoring.
        evidence: Supporting evidence from transcript or metrics.
        impact: Real-world communication impact.
        action: Clear, step-by-step guideline for the user.
        priority: Relative priority ('High Priority', 'Medium Priority', 'Low Priority').
        evidence_type: Classification of evidence.
        source_reference: Source turn or signal reference.
    """
    title: str
    what: str
    why: str
    evidence: str
    impact: str
    action: str
    priority: str = FeedbackPriority.HIGH.value
    evidence_type: str = EvidenceType.ANALYSIS_OBSERVATION.value
    source_reference: str = ""

    def __post_init__(self) -> None:
        if not self.title or not self.what or not self.why or not self.action:
            raise ValueError("ImprovementFeedbackItem requires title, what, why, and action.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert ImprovementFeedbackItem to dictionary."""
        return {
            "title": self.title,
            "what": self.what,
            "why": self.why,
            "evidence": self.evidence,
            "evidence_type": self.evidence_type,
            "source_reference": self.source_reference,
            "impact": self.impact,
            "action": self.action,
            "priority": self.priority,
        }


@dataclass
class PracticeAction:
    """
    High-level prioritized practical action to execute in next practice session.
    
    Attributes:
        title: Short action title.
        action: Concrete practical instruction.
        scenario_context: Context or mode relevance.
        priority: Action urgency level.
    """
    title: str
    action: str
    scenario_context: str
    priority: str = FeedbackPriority.HIGH.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert PracticeAction to dictionary."""
        return {
            "title": self.title,
            "action": self.action,
            "scenario_context": self.scenario_context,
            "priority": self.priority,
        }


@dataclass
class FeedbackResult:
    """
    Complete explainable feedback report synthesizing conversation intelligence and evaluation.
    """
    session_id: str
    mode: str
    difficulty: str
    overall_summary: str
    items: List[FeedbackItem] = field(default_factory=list)
    strengths: List[StrengthFeedbackItem] = field(default_factory=list)
    improvements: List[ImprovementFeedbackItem] = field(default_factory=list)
    priority_actions: List[PracticeAction] = field(default_factory=list)
    insufficient_evidence_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert complete FeedbackResult to dictionary."""
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "difficulty": self.difficulty,
            "overall_summary": self.overall_summary,
            "items": [item.to_dict() for item in self.items],
            "strengths": [s.to_dict() for s in self.strengths],
            "improvements": [imp.to_dict() for imp in self.improvements],
            "priority_actions": [pa.to_dict() for pa in self.priority_actions],
            "insufficient_evidence_notes": self.insufficient_evidence_notes,
        }
