"""
Evaluation Engine orchestrating dimension scoring, overall score synthesis, and explainability.
"""

import logging
from typing import List, Dict, Any, Optional

from src.intelligence.analysis_models import ConversationAnalysis
from src.scenarios.scenario_models import Scenario, Persona
from src.evaluation.evaluation_models import (
    EvaluationResult,
    ScoreDimension,
    ModeEvaluation,
    DimensionStatus,
)
from src.evaluation.mode_evaluators import MODE_EVALUATOR_REGISTRY, HRInterviewEvaluator

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """
    Central evaluation engine that computes deterministic, explainable performance evaluations
    from structured Phase 4 conversation evidence.
    """

    def evaluate(
        self,
        analysis: ConversationAnalysis,
        scenario: Optional[Scenario] = None,
        persona: Optional[Persona] = None,
    ) -> EvaluationResult:
        """
        Evaluate candidate performance based on conversation evidence.
        
        Args:
            analysis: Populated ConversationAnalysis instance from Phase 4.
            scenario: Optional Scenario definition.
            persona: Optional Persona definition.
            
        Returns:
            A complete EvaluationResult with dimensional scores, evidence, and rationale.
        """
        # 1. Obtain mode-specific evaluator
        evaluator = MODE_EVALUATOR_REGISTRY.get(analysis.mode, HRInterviewEvaluator())
        mode_eval: ModeEvaluation = evaluator.evaluate(analysis)

        dimensions: List[ScoreDimension] = mode_eval.dimensions

        # 2. Compute normalized overall score across evaluated dimensions
        evaluated_dims = [d for d in dimensions if d.is_evaluated()]
        insufficient_dims = [
            d.name for d in dimensions if d.status == DimensionStatus.INSUFFICIENT_EVIDENCE.value
        ]

        if not evaluated_dims:
            overall_score = 0.0
        else:
            total_weighted_points = sum(d.score * d.weight for d in evaluated_dims)
            total_weight = sum(d.weight for d in evaluated_dims)
            overall_score = (
                (total_weighted_points / total_weight) if total_weight > 0 else 0.0
            )

        clamped_overall = max(0.0, min(100.0, overall_score))

        # 3. Synthesize evidence-backed Strengths
        strengths: List[str] = []
        for d in evaluated_dims:
            if d.score >= 80.0:
                strengths.append(f"Strong performance in {d.name}: {d.rationale}")

        if analysis.total_filler_count == 0 and analysis.total_user_words > 20:
            strengths.append("High delivery fluency with zero detected vocal filler words.")
        if analysis.covered_expected_topics and not analysis.missing_expected_topics:
            strengths.append("Comprehensive scenario coverage; all configured expected topics were addressed.")
        if analysis.unanswered_questions_count == 0 and analysis.questions_detected:
            strengths.append("Consistent question responsiveness with all AI inquiries addressed.")

        # Default fallback if no specific high score met
        if not strengths:
            if analysis.user_message_count > 0:
                strengths.append(f"Completed {analysis.user_message_count} conversational turns.")
            else:
                strengths.append("Session initiated.")

        # 4. Synthesize evidence-backed Improvement Areas
        improvement_areas: List[str] = []
        for d in evaluated_dims:
            if d.score < 70.0:
                improvement_areas.append(f"Opportunity for refinement in {d.name}: {d.rationale}")

        if analysis.missing_expected_topics:
            missing_str = ", ".join(analysis.missing_expected_topics)
            improvement_areas.append(f"Expected scenario topic(s) not detected: {missing_str}.")

        if analysis.unanswered_questions_count > 0:
            improvement_areas.append(
                f"{analysis.unanswered_questions_count} AI inquiry(ies) appeared unaddressed or lacked concrete details."
            )

        if analysis.filler_percentage > 4.0:
            improvement_areas.append(
                f"Elevated filler word frequency ({analysis.filler_percentage:.1f}% of speech). Consider pausing instead of vocalizing hesitations."
            )

        if analysis.potential_contradictions:
            improvement_areas.append(
                "Ensure strict factual consistency across turns to avoid conflicting statements."
            )

        if not improvement_areas:
            improvement_areas.append("Maintain structured delivery and continue integrating concrete metrics in responses.")

        return EvaluationResult(
            session_id=analysis.session_id,
            mode=analysis.mode,
            difficulty=analysis.difficulty,
            overall_score=clamped_overall,
            max_score=100.0,
            dimensions=dimensions,
            strengths=strengths,
            improvement_areas=improvement_areas,
            insufficient_evidence_dimensions=insufficient_dims,
            mode_specific_evaluation=mode_eval,
        )
