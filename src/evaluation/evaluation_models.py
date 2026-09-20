"""
Evaluation and Scoring data models for Pitch Practice Partner.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class DimensionStatus(str, Enum):
    """Status of an evaluation dimension."""
    EVALUATED = "evaluated"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class ScoreDimension:
    """
    Individual evaluation dimension with score, weight, evidence, and rationale.
    
    Attributes:
        name: Name of the dimension (e.g., 'Question Handling', 'STAR Completeness').
        score: Computed score between 0.0 and 100.0 (if evaluated).
        max_score: Maximum achievable score (standardized to 100.0).
        weight: Relative weighting of this dimension in overall score calculation.
        status: Evaluation status ('evaluated', 'insufficient_evidence', 'not_applicable').
        evidence: List of factual observations supporting the score.
        rationale: Human-readable explanation of how evidence produced the score.
    """
    name: str
    score: float = 0.0
    max_score: float = 100.0
    weight: float = 1.0
    status: str = DimensionStatus.EVALUATED.value
    evidence: List[str] = field(default_factory=list)
    rationale: str = ""

    def __post_init__(self) -> None:
        """Validate score bounds and weight."""
        if self.max_score <= 0:
            raise ValueError("max_score must be greater than zero.")
        if self.score < 0.0 or self.score > self.max_score:
            raise ValueError(f"Score {self.score} must be between 0.0 and {self.max_score}.")
        if self.weight < 0.0:
            raise ValueError("Weight cannot be negative.")

    def is_evaluated(self) -> bool:
        """Check if this dimension has sufficient evidence to be scored."""
        return self.status == DimensionStatus.EVALUATED.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert ScoreDimension to dictionary."""
        return {
            "name": self.name,
            "score": round(self.score, 1) if self.is_evaluated() else None,
            "max_score": self.max_score,
            "weight": self.weight,
            "status": self.status,
            "evidence": self.evidence,
            "rationale": self.rationale,
        }


@dataclass
class ModeEvaluation:
    """
    Domain-specific evaluation metadata and notes for a practice mode.
    
    Attributes:
        mode: The practice mode evaluated.
        dimensions: List of mode-specific score dimensions.
        mode_notes: Contextual notes regarding domain expectations and limitations.
    """
    mode: str
    dimensions: List[ScoreDimension] = field(default_factory=list)
    mode_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ModeEvaluation to dictionary."""
        return {
            "mode": self.mode,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "mode_notes": self.mode_notes,
        }


@dataclass
class EvaluationResult:
    """
    Complete structured evaluation report for a practice session.
    Represents an explainable synthesis of conversation evidence into dimensional scores.
    """
    session_id: str
    mode: str
    difficulty: str
    overall_score: float
    max_score: float = 100.0
    dimensions: List[ScoreDimension] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    insufficient_evidence_dimensions: List[str] = field(default_factory=list)
    mode_specific_evaluation: Optional[ModeEvaluation] = None

    def __post_init__(self) -> None:
        """Validate overall score bounds."""
        if self.overall_score < 0.0 or self.overall_score > self.max_score:
            raise ValueError(f"Overall score {self.overall_score} must be between 0.0 and {self.max_score}.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert EvaluationResult to structured dictionary."""
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "difficulty": self.difficulty,
            "overall_score": round(self.overall_score, 1),
            "max_score": self.max_score,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "strengths": self.strengths,
            "improvement_areas": self.improvement_areas,
            "insufficient_evidence_dimensions": self.insufficient_evidence_dimensions,
            "mode_specific_evaluation": self.mode_specific_evaluation.to_dict()
            if self.mode_specific_evaluation
            else None,
        }
