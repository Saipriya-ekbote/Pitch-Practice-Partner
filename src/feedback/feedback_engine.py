"""
Feedback Engine orchestrating deterministic, evidence-backed explainable feedback.
Consumes Phase 4 ConversationAnalysis and Phase 5 EvaluationResult.
"""

import logging
from typing import List, Dict, Any, Optional

from src.intelligence.analysis_models import ConversationAnalysis
from src.evaluation.evaluation_models import EvaluationResult, ScoreDimension, DimensionStatus
from src.conversation.conversation_models import PracticeSession
from src.scenarios.scenario_models import Scenario, Persona
from src.feedback.feedback_models import (
    FeedbackResult,
    FeedbackItem,
    StrengthFeedbackItem,
    ImprovementFeedbackItem,
    PracticeAction,
    FeedbackPriority,
    EvidenceType,
)
from src.feedback.feedback_rules import explain_dimension

logger = logging.getLogger(__name__)


class FeedbackEngine:
    """
    Synthesizes Phase 4 conversation intelligence and Phase 5 evaluation scores
    into actionable, explainable feedback grounded in real conversation evidence.
    """

    def generate_feedback(
        self,
        analysis: ConversationAnalysis,
        evaluation: EvaluationResult,
        session: Optional[PracticeSession] = None,
        scenario: Optional[Scenario] = None,
        persona: Optional[Persona] = None,
    ) -> FeedbackResult:
        """
        Generate complete explainable feedback report.
        
        Args:
            analysis: Phase 4 ConversationAnalysis instance.
            evaluation: Phase 5 EvaluationResult instance.
            session: Optional active PracticeSession (for direct transcript excerpt extraction).
            scenario: Optional Scenario definition.
            persona: Optional Persona definition.
            
        Returns:
            A populated, deterministic FeedbackResult instance.
        """
        # 1. Generate explainable feedback item for each dimension
        feedback_items: List[FeedbackItem] = []
        for dim in evaluation.dimensions:
            item = explain_dimension(dim, analysis, session)
            feedback_items.append(item)

        # 2. Synthesize Evidence-Backed Strengths
        strengths: List[StrengthFeedbackItem] = []
        for item in feedback_items:
            if item.is_evaluated() and item.score is not None and item.score >= 80.0:
                strengths.append(
                    StrengthFeedbackItem(
                        title=f"Strong {item.dimension}",
                        what=item.what,
                        evidence=item.evidence,
                        impact=item.impact,
                        evidence_type=item.evidence_type,
                        source_reference=item.source_reference,
                    )
                )

        # Additional specific evidence-backed strengths
        if analysis.total_filler_count == 0 and analysis.total_user_words > 20:
            strengths.append(
                StrengthFeedbackItem(
                    title="High Delivery Fluency",
                    what="Zero vocal filler words were detected across candidate turns.",
                    evidence=f"Analysis observation: 0 vocal hesitations across {analysis.total_user_words} words.",
                    impact="Fluent, hesitation-free delivery projects composure and keeps the listener focused on your substance.",
                    evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
                    source_reference="Speech analysis",
                )
            )

        if analysis.covered_expected_topics and not analysis.missing_expected_topics:
            topics_str = ", ".join(analysis.covered_expected_topics)
            strengths.append(
                StrengthFeedbackItem(
                    title="Comprehensive Scenario Coverage",
                    what=f"All configured scenario topic domains were addressed ({topics_str}).",
                    evidence=f"Analysis observation: Covered {len(analysis.covered_expected_topics)} of {len(analysis.covered_expected_topics)} expected topics.",
                    impact="Thorough topic coverage satisfies all evaluation benchmarks.",
                    evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
                    source_reference="Topic analysis",
                )
            )

        # Fallback if no specific high score met
        if not strengths:
            if analysis.user_message_count > 0:
                strengths.append(
                    StrengthFeedbackItem(
                        title="Active Session Engagement",
                        what=f"Successfully completed {analysis.user_message_count} conversation turns ({analysis.total_user_words} total words spoken).",
                        evidence=f"Analysis observation: {analysis.user_message_count} candidate dialogue turns logged.",
                        impact="Consistent turn participation establishes the foundation for multi-turn communication practice.",
                        evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
                        source_reference="Session log",
                    )
                )
            else:
                strengths.append(
                    StrengthFeedbackItem(
                        title="Session Initialized",
                        what="Simulation environment configured and initialized.",
                        evidence="Analysis observation: Simulation scenario loaded.",
                        impact="Readiness to engage in conversational practice.",
                        evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
                        source_reference="System state",
                    )
                )

        # 3. Synthesize Actionable Improvement Areas
        improvements: List[ImprovementFeedbackItem] = []
        for item in feedback_items:
            if item.is_evaluated() and item.score is not None and item.score < 75.0:
                improvements.append(
                    ImprovementFeedbackItem(
                        title=f"Refine {item.dimension}",
                        what=item.what,
                        why=item.why,
                        evidence=item.evidence,
                        impact=item.impact,
                        action=item.action,
                        priority=item.priority,
                        evidence_type=item.evidence_type,
                        source_reference=item.source_reference,
                    )
                )

        # Additional specific gap improvements
        if analysis.unanswered_questions_count > 0:
            improvements.append(
                ImprovementFeedbackItem(
                    title="Direct Question Answering",
                    what=f"{analysis.unanswered_questions_count} inquiry(ies) from the persona received incomplete answers.",
                    why="Diverging before answering the prompt leaves the question unresolved.",
                    evidence=f"Analysis observation: {analysis.unanswered_questions_count} unaddressed questions detected.",
                    impact="Evaluators may interpret unaddressed inquiries as lack of preparation or evasion.",
                    action="Answer the question directly in your opening sentence before adding background explanation.",
                    priority=FeedbackPriority.HIGH.value,
                    evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
                    source_reference="Question detector",
                )
            )

        if analysis.filler_percentage > 3.5:
            improvements.append(
                ImprovementFeedbackItem(
                    title="Hesitation Marker Reduction",
                    what=f"Elevated filler word density: {analysis.filler_percentage:.1f}% of speech ({analysis.total_filler_count} fillers).",
                    why="High filler frequency disrupts delivery rhythm and dilutes message clarity.",
                    evidence=f"Analysis observation: {analysis.total_filler_count} filler words detected.",
                    impact="In high-stakes communication, excessive vocal fillers reduce perceived authority.",
                    action="Pause silently for 1 full second to organize your thoughts instead of vocalizing 'um' or 'like'.",
                    priority=FeedbackPriority.MEDIUM.value,
                    evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
                    source_reference="Linguistic analysis",
                )
            )

        # Fallback if no specific gap met
        if not improvements:
            improvements.append(
                ImprovementFeedbackItem(
                    title="Advanced Refinement",
                    what="Demonstrated strong baseline performance across core evaluated dimensions.",
                    why="All evaluated scores met or exceeded competency thresholds.",
                    evidence="Analysis observation: All dimensions scored ≥ 75.0.",
                    impact="Continuous refinement in advanced scenarios builds peak readiness.",
                    action="Increase difficulty to Advanced or challenge yourself with skeptical personas to test resilience under pressure.",
                    priority=FeedbackPriority.LOW.value,
                    evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
                    source_reference="Evaluation synthesis",
                )
            )

        # 4. Extract Top Prioritized Practice Actions
        priority_actions: List[PracticeAction] = []
        # High priority actions first, then medium
        sorted_improvements = sorted(
            improvements,
            key=lambda x: (
                0 if x.priority == FeedbackPriority.HIGH.value
                else (1 if x.priority == FeedbackPriority.MEDIUM.value else 2)
            )
        )

        seen_actions = set()
        for imp in sorted_improvements:
            if imp.action not in seen_actions:
                seen_actions.add(imp.action)
                priority_actions.append(
                    PracticeAction(
                        title=imp.title,
                        action=imp.action,
                        scenario_context=f"{evaluation.mode} ({evaluation.difficulty})",
                        priority=imp.priority,
                    )
                )
            if len(priority_actions) >= 4:
                break

        # 5. Compile Insufficient Evidence Notes
        insufficient_notes: List[str] = []
        for item in feedback_items:
            if item.status == DimensionStatus.INSUFFICIENT_EVIDENCE.value:
                insufficient_notes.append(
                    f"{item.dimension}: {item.what} ({item.action})"
                )

        # 6. Synthesize Overall Summary
        top_str = strengths[0].title if strengths else "Engagement"
        top_imp = improvements[0].title if improvements else "Delivery Refinement"
        
        if evaluation.overall_score >= 85.0:
            performance_tier = "Strong Performance"
            tier_desc = "Demonstrated clear, structured communication aligned with scenario requirements."
        elif evaluation.overall_score >= 65.0:
            performance_tier = "Solid Foundation with Actionable Opportunities"
            tier_desc = "Good core answers with specific areas identified for structural and delivery refinement."
        else:
            performance_tier = "Developing Communication"
            tier_desc = "Key foundational competencies require structured focus in subsequent practice turns."

        overall_summary = (
            f"**{performance_tier} ({evaluation.overall_score:.1f}/100 in {evaluation.mode}):** {tier_desc} "
            f"Key strength: **{top_str}**. Primary focus for next session: **{top_imp}**."
        )

        return FeedbackResult(
            session_id=analysis.session_id,
            mode=analysis.mode,
            difficulty=analysis.difficulty,
            overall_summary=overall_summary,
            items=feedback_items,
            strengths=strengths,
            improvements=improvements,
            priority_actions=priority_actions,
            insufficient_evidence_notes=insufficient_notes,
        )
