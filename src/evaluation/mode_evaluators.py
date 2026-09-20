"""
Mode-specific evaluators mapping domain evidence to specialized evaluation dimensions.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from src.intelligence.analysis_models import ConversationAnalysis
from src.evaluation.evaluation_models import ScoreDimension, ModeEvaluation, DimensionStatus
from src.evaluation.scoring_rules import (
    calculate_question_handling_score,
    calculate_topic_coverage_score,
    calculate_communication_score,
    calculate_relevance_score,
    calculate_objection_handling_score,
)


class BaseModeEvaluator(ABC):
    """Abstract Strategy interface for domain-specific evaluation."""

    @abstractmethod
    def evaluate(self, analysis: ConversationAnalysis) -> ModeEvaluation:
        pass


# ==============================================================================
# 1. HR Interview Evaluator
# ==============================================================================

class HRInterviewEvaluator(BaseModeEvaluator):
    """Evaluates behavioral interviews with focus on STAR methodology and concrete examples."""

    def evaluate(self, analysis: ConversationAnalysis) -> ModeEvaluation:
        dimensions: List[ScoreDimension] = []
        indicators = analysis.mode_specific_analysis.indicators if analysis.mode_specific_analysis else {}

        # 1. STAR Framework Completeness (Weight 1.5)
        star_components = indicators.get("star_components", {})
        if not star_components or analysis.user_message_count == 0:
            star_dim = ScoreDimension(
                name="STAR Framework Completeness",
                score=0.0,
                weight=1.5,
                status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
                evidence=["No behavioral responses available to evaluate STAR framework."],
                rationale="Insufficient evidence: No user responses recorded.",
            )
        else:
            detected_count = sum(1 for v in star_components.values() if v == "detected")
            star_score = (detected_count / 4.0) * 100.0
            evidence = [f"{comp}: {status.capitalize()}" for comp, status in star_components.items()]
            star_dim = ScoreDimension(
                name="STAR Framework Completeness",
                score=star_score,
                weight=1.5,
                status=DimensionStatus.EVALUATED.value,
                evidence=evidence,
                rationale=f"Detected {detected_count} of 4 STAR components (Situation, Task, Action, Result).",
            )
        dimensions.append(star_dim)

        # 2. Example Specificity & Metrics (Weight 1.0)
        if analysis.user_message_count == 0:
            spec_dim = ScoreDimension(
                name="Example Specificity & Outcomes",
                score=0.0,
                weight=1.0,
                status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
                evidence=["No response data."],
                rationale="Insufficient evidence.",
            )
        else:
            has_metric = indicators.get("specific_metrics_provided") == "detected"
            spec_score = 90.0 if has_metric else 65.0
            spec_dim = ScoreDimension(
                name="Example Specificity & Outcomes",
                score=spec_score,
                weight=1.0,
                status=DimensionStatus.EVALUATED.value,
                evidence=[
                    f"Measurable metrics/timeline details: {'Detected' if has_metric else 'Not detected'}"
                ],
                rationale="Concrete measurable outcomes were included in behavioral examples."
                if has_metric
                else "Behavioral responses used qualitative descriptions without specific metrics or timelines.",
            )
        dimensions.append(spec_dim)

        # 3. Question Handling (Weight 1.2)
        dimensions.append(calculate_question_handling_score(analysis, weight=1.2))

        # 4. Communication Clarity & Fluency (Weight 1.0)
        dimensions.append(calculate_communication_score(analysis, weight=1.0))

        # 5. Scenario Alignment & Topic Coverage (Weight 1.0)
        dimensions.append(calculate_topic_coverage_score(analysis, weight=1.0))

        notes = [
            "HR evaluation emphasizes the STAR method (Situation, Task, Action, Result) and concrete personal ownership.",
            "Psychological confidence and personality are intentionally not evaluated.",
        ]
        return ModeEvaluation(mode="HR Interview", dimensions=dimensions, mode_notes=notes)


# ==============================================================================
# 2. Technical Interview Evaluator
# ==============================================================================

class TechnicalInterviewEvaluator(BaseModeEvaluator):
    """Evaluates technical interviews for complexity discussion, data structures, and edge cases."""

    def evaluate(self, analysis: ConversationAnalysis) -> ModeEvaluation:
        dimensions: List[ScoreDimension] = []
        indicators = analysis.mode_specific_analysis.indicators if analysis.mode_specific_analysis else {}
        tech_concepts = indicators.get("technical_concepts", {})

        if not tech_concepts or analysis.user_message_count == 0:
            dimensions.append(
                ScoreDimension(
                    name="Technical Concept Breadth",
                    score=0.0,
                    weight=1.5,
                    status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
                    evidence=["No technical responses recorded."],
                    rationale="Insufficient evidence.",
                )
            )
        else:
            # 1. Technical Concept Breadth (Weight 1.5)
            detected_c = sum(1 for v in tech_concepts.values() if v == "detected")
            concept_score = (detected_c / max(1, len(tech_concepts))) * 100.0
            dimensions.append(
                ScoreDimension(
                    name="Technical Concept Breadth",
                    score=concept_score,
                    weight=1.5,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[f"{k}: {v.capitalize()}" for k, v in tech_concepts.items()],
                    rationale=f"Candidate addressed {detected_c} of {len(tech_concepts)} core technical concept categories.",
                )
            )

            # 2. Complexity Analysis Rigor (Weight 1.2)
            time_c = tech_concepts.get("Time Complexity") == "detected"
            space_c = tech_concepts.get("Space / Memory Overhead") == "detected"
            comp_score = 100.0 if (time_c and space_c) else (65.0 if (time_c or space_c) else 35.0)
            dimensions.append(
                ScoreDimension(
                    name="Complexity Analysis Rigor",
                    score=comp_score,
                    weight=1.2,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[
                        f"Time complexity analysis: {'Detected' if time_c else 'Not detected'}",
                        f"Space/memory overhead analysis: {'Detected' if space_c else 'Not detected'}",
                    ],
                    rationale="Candidate articulated both time and space complexity trade-offs."
                    if (time_c and space_c)
                    else "Partial or missing complexity trade-off discussion.",
                )
            )

            # 3. Edge Case & Boundary Reasoning (Weight 1.0)
            edge_c = tech_concepts.get("Edge Cases & Boundary Conditions") == "detected"
            edge_score = 90.0 if edge_c else 50.0
            dimensions.append(
                ScoreDimension(
                    name="Edge Case & Boundary Reasoning",
                    score=edge_score,
                    weight=1.0,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[f"Edge cases / error handling: {'Detected' if edge_c else 'Not detected'}"],
                    rationale="Candidate explicitly discussed boundary conditions, empty inputs, or concurrency."
                    if edge_c
                    else "No explicit discussion of boundary conditions or failure modes detected.",
                )
            )

        # Standard shared dimensions
        dimensions.append(calculate_question_handling_score(analysis, weight=1.2))
        dimensions.append(calculate_communication_score(analysis, weight=1.0))

        notes = [
            "Technical evaluation measures presence of complexity trade-offs, data structures, and edge cases.",
            "Concept mentions are distinguished from deterministic algorithmic proof.",
        ]
        return ModeEvaluation(mode="Technical Interview", dimensions=dimensions, mode_notes=notes)


# ==============================================================================
# 3. Client Pitch Evaluator
# ==============================================================================

class ClientPitchEvaluator(BaseModeEvaluator):
    """Evaluates executive and client pitches for value proposition, ROI, security, and objections."""

    def evaluate(self, analysis: ConversationAnalysis) -> ModeEvaluation:
        dimensions: List[ScoreDimension] = []
        indicators = analysis.mode_specific_analysis.indicators if analysis.mode_specific_analysis else {}
        pitch_comps = indicators.get("pitch_components", {})

        if not pitch_comps or analysis.user_message_count == 0:
            dimensions.append(
                ScoreDimension(
                    name="Value Proposition & Business Impact",
                    score=0.0,
                    weight=1.5,
                    status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
                    evidence=["No pitch responses recorded."],
                    rationale="Insufficient evidence.",
                )
            )
        else:
            # 1. Value Proposition & Business Impact (Weight 1.5)
            vp = pitch_comps.get("Value Proposition") == "detected"
            roi = pitch_comps.get("Cost & ROI Justification") == "detected"
            vp_score = 95.0 if (vp and roi) else (70.0 if (vp or roi) else 40.0)
            dimensions.append(
                ScoreDimension(
                    name="Value Proposition & Business Impact",
                    score=vp_score,
                    weight=1.5,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[
                        f"Value proposition articulated: {'Yes' if vp else 'No'}",
                        f"Cost/ROI financial justification: {'Yes' if roi else 'No'}",
                    ],
                    rationale="Clearly articulated customer value proposition and financial return."
                    if (vp and roi)
                    else "Partially articulated value proposition with limited financial metrics.",
                )
            )

            # 2. Security, Compliance & Scalability (Weight 1.2)
            sec = pitch_comps.get("Security & Compliance") == "detected"
            scale = pitch_comps.get("Scalability & Performance") == "detected"
            sec_score = 95.0 if (sec and scale) else (70.0 if (sec or scale) else 45.0)
            dimensions.append(
                ScoreDimension(
                    name="Enterprise Security & Scalability",
                    score=sec_score,
                    weight=1.2,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[
                        f"Security/compliance safeguards: {'Detected' if sec else 'Not detected'}",
                        f"Scalability/SLA guarantees: {'Detected' if scale else 'Not detected'}",
                    ],
                    rationale="Addressed enterprise requirements including security, data privacy, and SLA performance.",
                )
            )

        # 3. Objection Handling (Weight 1.5)
        dimensions.append(calculate_objection_handling_score(analysis, weight=1.5))

        # 4. Question Handling (Weight 1.0)
        dimensions.append(calculate_question_handling_score(analysis, weight=1.0))

        # 5. Communication Clarity (Weight 1.0)
        dimensions.append(calculate_communication_score(analysis, weight=1.0))

        notes = [
            "Pitch evaluation measures business value communication, ROI evidence, and handling of executive objections.",
        ]
        return ModeEvaluation(mode="Client Pitch", dimensions=dimensions, mode_notes=notes)


# ==============================================================================
# 4. Project Viva Evaluator
# ==============================================================================

class ProjectVivaEvaluator(BaseModeEvaluator):
    """Evaluates academic defenses for architectural justification, methodology, and limitations."""

    def evaluate(self, analysis: ConversationAnalysis) -> ModeEvaluation:
        dimensions: List[ScoreDimension] = []
        indicators = analysis.mode_specific_analysis.indicators if analysis.mode_specific_analysis else {}
        viva_comps = indicators.get("viva_components", {})

        if not viva_comps or analysis.user_message_count == 0:
            dimensions.append(
                ScoreDimension(
                    name="Architecture & Stack Justification",
                    score=0.0,
                    weight=1.5,
                    status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
                    evidence=["No viva responses recorded."],
                    rationale="Insufficient evidence.",
                )
            )
        else:
            # 1. Architecture & Stack Justification (Weight 1.5)
            arch = viva_comps.get("Architecture & Design Justification") == "detected"
            stack = viva_comps.get("Technology Stack Rationale") == "detected"
            arch_score = 95.0 if (arch and stack) else (70.0 if (arch or stack) else 40.0)
            dimensions.append(
                ScoreDimension(
                    name="Architecture & Stack Justification",
                    score=arch_score,
                    weight=1.5,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[
                        f"Architecture design patterns: {'Detected' if arch else 'Not detected'}",
                        f"Technology trade-off rationale: {'Detected' if stack else 'Not detected'}",
                    ],
                    rationale="Candidate defended system architecture and justified tech stack choices over alternatives.",
                )
            )

            # 2. Methodology & Validation Rigor (Weight 1.5)
            meth = viva_comps.get("Methodology & Experimental Rigor") == "detected"
            meth_score = 90.0 if meth else 50.0
            dimensions.append(
                ScoreDimension(
                    name="Methodology & Validation Rigor",
                    score=meth_score,
                    weight=1.5,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[f"Experimental validation metrics/baseline: {'Detected' if meth else 'Not detected'}"],
                    rationale="Candidate explained experimental methodology, metrics, and dataset validation."
                    if meth
                    else "Methodology validation details were limited.",
                )
            )

            # 3. Awareness of Limitations & Constraints (Weight 1.0)
            lim = viva_comps.get("Awareness of Limitations") == "detected"
            lim_score = 90.0 if lim else 55.0
            dimensions.append(
                ScoreDimension(
                    name="Awareness of Limitations",
                    score=lim_score,
                    weight=1.0,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[f"System limitations / future work acknowledged: {'Yes' if lim else 'No'}"],
                    rationale="Demonstrated honest, academic appraisal of project constraints and future improvements."
                    if lim
                    else "No explicit acknowledgment of design limitations or trade-offs.",
                )
            )

        # Standard shared dimensions
        dimensions.append(calculate_question_handling_score(analysis, weight=1.2))
        dimensions.append(calculate_communication_score(analysis, weight=1.0))

        notes = [
            "Project Viva evaluation measures design justification, experimental rigor, and honest self-critique.",
        ]
        return ModeEvaluation(mode="Project Viva", dimensions=dimensions, mode_notes=notes)


# ==============================================================================
# 5. Group Discussion Evaluator
# ==============================================================================

class GroupDiscussionEvaluator(BaseModeEvaluator):
    """Evaluates collaborative group discussions for synthesis, nuanced viewpoints, and debate dynamics."""

    def evaluate(self, analysis: ConversationAnalysis) -> ModeEvaluation:
        dimensions: List[ScoreDimension] = []
        indicators = analysis.mode_specific_analysis.indicators if analysis.mode_specific_analysis else {}
        gd_signals = indicators.get("discussion_dynamics", {})

        if not gd_signals or analysis.user_message_count == 0:
            dimensions.append(
                ScoreDimension(
                    name="Argument Quality & Evidence",
                    score=0.0,
                    weight=1.5,
                    status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
                    evidence=["No discussion dialogue recorded."],
                    rationale="Insufficient evidence.",
                )
            )
        else:
            # 1. Argument Quality & Evidence (Weight 1.5)
            evi = gd_signals.get("Evidence-Backed Reasoning") == "detected"
            counter = gd_signals.get("Respectful Counter-Argument / Nuance") == "detected"
            arg_score = 95.0 if (evi and counter) else (70.0 if (evi or counter) else 45.0)
            dimensions.append(
                ScoreDimension(
                    name="Argument Quality & Evidence",
                    score=arg_score,
                    weight=1.5,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[
                        f"Evidence-backed data points: {'Detected' if evi else 'Not detected'}",
                        f"Nuanced counter-arguments: {'Detected' if counter else 'Not detected'}",
                    ],
                    rationale="Candidate offered nuanced perspectives supported by rationale.",
                )
            )

            # 2. Synthesis & Collaborative Dynamics (Weight 1.5)
            agree = gd_signals.get("Constructive Agreement / Building On Ideas") == "detected"
            synth = gd_signals.get("Synthesis / Common Ground") == "detected"
            collab_score = 95.0 if (agree and synth) else (70.0 if (agree or synth) else 50.0)
            dimensions.append(
                ScoreDimension(
                    name="Synthesis & Collaborative Dynamics",
                    score=collab_score,
                    weight=1.5,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[
                        f"Building on others' ideas: {'Detected' if agree else 'Not detected'}",
                        f"Synthesizing consensus: {'Detected' if synth else 'Not detected'}",
                    ],
                    rationale="Demonstrated collaborative moderation by synthesizing arguments and finding common ground.",
                )
            )

        # 3. Question & Moderator Engagement (Weight 1.0)
        dimensions.append(calculate_question_handling_score(analysis, weight=1.0))

        # 4. Relevance & Conversational Substance (Weight 1.0)
        dimensions.append(calculate_relevance_score(analysis, weight=1.0))

        # 5. Communication & Repetition Control (Weight 1.0)
        dimensions.append(calculate_communication_score(analysis, weight=1.0))

        notes = [
            "Group discussion evaluation balances active contribution with constructive listening and synthesis.",
        ]
        return ModeEvaluation(mode="Group Discussion", dimensions=dimensions, mode_notes=notes)


# ==============================================================================
# 6. Managerial Interview Evaluator
# ==============================================================================

class ManagerialInterviewEvaluator(BaseModeEvaluator):
    """Evaluates leadership interviews for conflict mediation, ownership, and prioritization."""

    def evaluate(self, analysis: ConversationAnalysis) -> ModeEvaluation:
        dimensions: List[ScoreDimension] = []
        indicators = analysis.mode_specific_analysis.indicators if analysis.mode_specific_analysis else {}
        mgr_signals = indicators.get("leadership_signals", {})

        if not mgr_signals or analysis.user_message_count == 0:
            dimensions.append(
                ScoreDimension(
                    name="Leadership Empathy & Coaching",
                    score=0.0,
                    weight=1.5,
                    status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
                    evidence=["No managerial dialogue recorded."],
                    rationale="Insufficient evidence.",
                )
            )
        else:
            # 1. Leadership Empathy & 1-on-1 Coaching (Weight 1.5)
            emp = mgr_signals.get("Empathetic Leadership & 1-on-1 Communication") == "detected"
            emp_score = 90.0 if emp else 55.0
            dimensions.append(
                ScoreDimension(
                    name="Leadership Empathy & Coaching",
                    score=emp_score,
                    weight=1.5,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[f"1-on-1 communication / empathy: {'Detected' if emp else 'Not detected'}"],
                    rationale="Demonstrated empathetic people leadership, active listening, and 1-on-1 coaching approaches."
                    if emp
                    else "Responses focused on operational tasks rather than people leadership.",
                )
            )

            # 2. Conflict Mediation & De-escalation (Weight 1.5)
            conf = mgr_signals.get("Conflict Mediation & De-escalation") == "detected"
            conf_score = 90.0 if conf else 55.0
            dimensions.append(
                ScoreDimension(
                    name="Conflict Mediation & De-escalation",
                    score=conf_score,
                    weight=1.5,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[f"Conflict de-escalation / mediation: {'Detected' if conf else 'Not detected'}"],
                    rationale="Articulated clear steps to mediate engineering disagreements and restore alignment."
                    if conf
                    else "Limited conflict resolution framework described.",
                )
            )

            # 3. Prioritization & Ownership (Weight 1.2)
            prio = mgr_signals.get("Prioritization Frameworks") == "detected"
            own = mgr_signals.get("Ownership & Accountability") == "detected"
            prio_score = 95.0 if (prio and own) else (70.0 if (prio or own) else 50.0)
            dimensions.append(
                ScoreDimension(
                    name="Prioritization & Ownership",
                    score=prio_score,
                    weight=1.2,
                    status=DimensionStatus.EVALUATED.value,
                    evidence=[
                        f"Prioritization frameworks (e.g. RICE/triage): {'Detected' if prio else 'Not detected'}",
                        f"Personal ownership & accountability: {'Detected' if own else 'Not detected'}",
                    ],
                    rationale="Utilized structured prioritization frameworks while taking personal responsibility.",
                )
            )

        # Standard shared dimensions
        dimensions.append(calculate_question_handling_score(analysis, weight=1.0))
        dimensions.append(calculate_communication_score(analysis, weight=1.0))

        notes = [
            "Managerial evaluation emphasizes empathetic team coaching, prioritization rigor, and stakeholder transparency.",
        ]
        return ModeEvaluation(mode="Managerial Interview", dimensions=dimensions, mode_notes=notes)


MODE_EVALUATOR_REGISTRY: Dict[str, BaseModeEvaluator] = {
    "HR Interview": HRInterviewEvaluator(),
    "Technical Interview": TechnicalInterviewEvaluator(),
    "Client Pitch": ClientPitchEvaluator(),
    "Project Viva": ProjectVivaEvaluator(),
    "Group Discussion": GroupDiscussionEvaluator(),
    "Managerial Interview": ManagerialInterviewEvaluator(),
}
