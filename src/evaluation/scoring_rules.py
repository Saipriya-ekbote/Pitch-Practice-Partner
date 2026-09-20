"""
Centralized scoring rules and deterministic mathematical formulas for Pitch Practice Partner.
Translates Phase 4 conversation evidence into explainable dimensional score models.
"""

from typing import List, Dict, Any, Optional

from src.intelligence.analysis_models import ConversationAnalysis
from src.evaluation.evaluation_models import ScoreDimension, DimensionStatus


# ==============================================================================
# 1. Question Handling Scoring Rule
# ==============================================================================

def calculate_question_handling_score(
    analysis: ConversationAnalysis, weight: float = 1.0
) -> ScoreDimension:
    """
    Evaluate how effectively the candidate addressed questions posed by the AI persona.
    
    Formula:
      weighted_answered = (addressed * 1.0) + (partially_addressed * 0.5) + (unaddressed * 0.0)
      score = (weighted_answered / total_questions) * 100.0
    """
    total_q = len(analysis.questions_detected)
    if total_q == 0:
        return ScoreDimension(
            name="Question Handling",
            score=0.0,
            weight=weight,
            status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
            evidence=["No distinct questions were detected in the conversation transcript."],
            rationale="Insufficient evidence: No questions posed by AI to evaluate.",
        )

    addressed = sum(1 for q in analysis.questions_detected if q.status == "addressed")
    partially = sum(1 for q in analysis.questions_detected if q.status == "partially_addressed")
    unaddressed = sum(1 for q in analysis.questions_detected if q.status == "unaddressed")

    weighted_score = ((addressed * 1.0) + (partially * 0.5)) / total_q * 100.0
    clamped_score = max(0.0, min(100.0, weighted_score))

    evidence = [
        f"Turn {q.turn_number}: \"{q.question_text[:60]}...\" — [{q.status.replace('_', ' ').capitalize()}]"
        for q in analysis.questions_detected
    ]

    rationale = (
        f"Candidate addressed {addressed} of {total_q} questions directly"
        + (f" and {partially} partially." if partially else ".")
        + (f" {unaddressed} question(s) appeared unaddressed." if unaddressed else "")
    )

    return ScoreDimension(
        name="Question Handling",
        score=clamped_score,
        weight=weight,
        status=DimensionStatus.EVALUATED.value,
        evidence=evidence,
        rationale=rationale,
    )


# ==============================================================================
# 2. Topic Coverage & Scenario Alignment Scoring Rule
# ==============================================================================

def calculate_topic_coverage_score(
    analysis: ConversationAnalysis, weight: float = 1.0
) -> ScoreDimension:
    """
    Evaluate candidate coverage of expected scenario competencies and topics.
    
    Formula:
      score = (covered_expected_topics / total_expected_topics) * 100.0
    """
    total_expected = len(analysis.covered_expected_topics) + len(analysis.missing_expected_topics)
    if total_expected == 0:
        return ScoreDimension(
            name="Scenario Alignment & Topic Coverage",
            score=0.0,
            weight=weight,
            status=DimensionStatus.NOT_APPLICABLE.value,
            evidence=["No specific expected topics configured for this scenario."],
            rationale="Not applicable: Scenario did not define expected topic benchmarks.",
        )

    covered_count = len(analysis.covered_expected_topics)
    coverage_score = (covered_count / total_expected) * 100.0
    clamped_score = max(0.0, min(100.0, coverage_score))

    evidence = [f"Covered: {t}" for t in analysis.covered_expected_topics] + [
        f"Missing: {t}" for t in analysis.missing_expected_topics
    ]

    rationale = f"Candidate covered {covered_count} of {total_expected} expected scenario topics ({clamped_score:.0f}% coverage)."

    return ScoreDimension(
        name="Scenario Alignment & Topic Coverage",
        score=clamped_score,
        weight=weight,
        status=DimensionStatus.EVALUATED.value,
        evidence=evidence,
        rationale=rationale,
    )


# ==============================================================================
# 3. Communication & Fluency Scoring Rule
# ==============================================================================

def calculate_communication_score(
    analysis: ConversationAnalysis, weight: float = 1.0
) -> ScoreDimension:
    """
    Evaluate measurable language signals (vocal fillers, excessive phrase repetition, response length).
    
    Formula:
      base = 100.0
      filler_penalty = min(35.0, filler_percentage * 5.0)
      repetition_penalty = min(20.0, len(repeated_phrases) * 5.0)
      short_penalty = 15.0 (if avg_words_per_response < 10)
      score = max(0.0, base - filler_penalty - repetition_penalty - short_penalty)
    """
    if analysis.user_message_count == 0 or analysis.total_user_words == 0:
        return ScoreDimension(
            name="Communication & Fluency",
            score=0.0,
            weight=weight,
            status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
            evidence=["No user responses available to measure communication features."],
            rationale="Insufficient evidence: No candidate speech data recorded.",
        )

    base = 100.0
    filler_penalty = min(35.0, analysis.filler_percentage * 5.0)
    repetition_penalty = min(20.0, len(analysis.repeated_phrases) * 5.0)
    
    short_penalty = 15.0 if analysis.avg_words_per_response < 10.0 else 0.0

    raw_score = base - filler_penalty - repetition_penalty - short_penalty
    clamped_score = max(0.0, min(100.0, raw_score))

    evidence: List[str] = [
        f"Filler words: {analysis.total_filler_count} detected ({analysis.filler_percentage:.1f}% of total words)",
        f"Average response length: {analysis.avg_words_per_response:.1f} words/turn",
    ]
    if analysis.repeated_phrases:
        evidence.append(f"Repeated phrases: {len(analysis.repeated_phrases)} detected")

    rationale_parts = []
    if analysis.total_filler_count == 0:
        rationale_parts.append("Clean delivery with zero filler words detected.")
    else:
        rationale_parts.append(f"{analysis.total_filler_count} filler words ({analysis.filler_percentage:.1f}% frequency).")

    if analysis.repeated_phrases:
        rationale_parts.append(f"{len(analysis.repeated_phrases)} repeated phrase(s) noted.")

    if short_penalty > 0:
        rationale_parts.append("Average response length was very brief (< 10 words).")

    return ScoreDimension(
        name="Communication & Fluency",
        score=clamped_score,
        weight=weight,
        status=DimensionStatus.EVALUATED.value,
        evidence=evidence,
        rationale=" ".join(rationale_parts),
    )


# ==============================================================================
# 4. Relevance & Substance Scoring Rule
# ==============================================================================

def calculate_relevance_score(
    analysis: ConversationAnalysis, weight: float = 1.0
) -> ScoreDimension:
    """
    Evaluate conversational substance, length appropriateness, and absence of logical contradictions.
    """
    if analysis.user_message_count == 0 or not analysis.response_features:
        return ScoreDimension(
            name="Relevance & Substance",
            score=0.0,
            weight=weight,
            status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
            evidence=["No user responses available."],
            rationale="Insufficient evidence: No dialogue submitted.",
        )

    # Ratio of medium or long responses
    medium_or_long = sum(1 for rf in analysis.response_features if rf.length_category in {"medium", "long"})
    substance_ratio = medium_or_long / len(analysis.response_features)


    base = 70.0 + (substance_ratio * 30.0)

    # Contradiction penalty
    contra_count = len(analysis.potential_contradictions)
    contra_penalty = min(40.0, contra_count * 20.0)

    clamped_score = max(0.0, min(100.0, base - contra_penalty))

    evidence = [
        f"Response length categories: {medium_or_long} of {len(analysis.response_features)} turns were structured/substantive.",
    ]
    if analysis.topics_discussed:
        evidence.append(f"Discussed topic domains: {', '.join(analysis.topics_discussed)}")
    if analysis.potential_contradictions:
        evidence.append(f"Contradictions detected: {contra_count}")

    rationale = (
        f"{substance_ratio * 100:.0f}% of responses provided substantive detail."
        + (f" {contra_count} potential contradiction(s) noted." if contra_count else "")
    )

    return ScoreDimension(
        name="Relevance & Substance",
        score=clamped_score,
        weight=weight,
        status=DimensionStatus.EVALUATED.value,
        evidence=evidence,
        rationale=rationale,
    )


# ==============================================================================
# 5. Objection Handling Scoring Rule
# ==============================================================================

def calculate_objection_handling_score(
    analysis: ConversationAnalysis, weight: float = 1.0
) -> ScoreDimension:
    """
    Evaluate whether persona objections or critical inquiries were addressed with evidence.
    """
    if not analysis.objections_evidence:
        return ScoreDimension(
            name="Objection Handling",
            score=0.0,
            weight=weight,
            status=DimensionStatus.NOT_APPLICABLE.value,
            evidence=["No critical objections were raised by the AI persona in this session."],
            rationale="Not applicable: No explicit pushback or objections voiced by the persona.",
        )

    total_objections = len(analysis.objections_evidence)
    addressed = sum(1 for o in analysis.objections_evidence if o.addressed)

    score = (addressed / total_objections) * 100.0
    clamped_score = max(0.0, min(100.0, score))

    evidence = [
        f"Objection: '{o.objection_type}' — [{'Addressed' if o.addressed else 'Unaddressed'}]"
        for o in analysis.objections_evidence
    ]

    rationale = f"Candidate addressed {addressed} of {total_objections} persona objections with relevant evidence."

    return ScoreDimension(
        name="Objection Handling",
        score=clamped_score,
        weight=weight,
        status=DimensionStatus.EVALUATED.value,
        evidence=evidence,
        rationale=rationale,
    )
