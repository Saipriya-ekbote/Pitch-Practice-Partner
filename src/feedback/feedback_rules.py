"""
Feedback rules mapping conversation intelligence and evaluation dimensions to explainable feedback.
Follows the WHAT / WHY / EVIDENCE / IMPACT / ACTION framework.
Ensures 100% deterministic, evidence-grounded, and language-objective feedback.
"""

from typing import Optional, List, Dict, Any, Tuple
from src.intelligence.analysis_models import ConversationAnalysis
from src.evaluation.evaluation_models import ScoreDimension, DimensionStatus
from src.conversation.conversation_models import PracticeSession
from src.feedback.feedback_models import (
    FeedbackItem,
    StrengthFeedbackItem,
    ImprovementFeedbackItem,
    PracticeAction,
    FeedbackPriority,
    EvidenceType,
    EvidenceConfidence,
)
from src.feedback.evidence_utils import (
    extract_user_turn_snippet,
    find_matching_user_snippet,
    extract_first_user_snippet,
    format_evidence_display,
    truncate_text,
)


def _determine_priority(score: Optional[float], has_critical_gap: bool = False) -> str:
    """Assign deterministic, explainable priority based on score and gap severity."""
    if score is None:
        return FeedbackPriority.LOW.value
    if has_critical_gap or score < 65.0:
        return FeedbackPriority.HIGH.value
    if score < 80.0:
        return FeedbackPriority.MEDIUM.value
    return FeedbackPriority.LOW.value


# ==============================================================================
# Dimension Rules: Common Dimensions
# ==============================================================================

def explain_question_handling(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Generate explainable feedback for Question Handling."""
    if dim.status == DimensionStatus.INSUFFICIENT_EVIDENCE.value:
        return FeedbackItem(
            dimension=dim.name,
            status=dim.status,
            score=None,
            max_score=dim.max_score,
            what="No questions from the interviewer or persona were detected during this session.",
            why="Question responsiveness cannot be scored without conversational inquiries.",
            evidence="Analysis observation: 0 questions logged in conversation transcript.",
            evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
            source_reference="Transcript",
            impact="Handling follow-up questions directly is essential to demonstrating subject mastery and active listening in any interview or pitch.",
            action="In your next session, practice a scenario where the persona asks questions so your inquiry handling can be evaluated.",
            priority=FeedbackPriority.LOW.value,
            confidence=EvidenceConfidence.INSUFFICIENT.value,
        )

    score = dim.score
    total_q = len(analysis.questions_detected)
    addressed = sum(1 for q in analysis.questions_detected if q.status == "addressed")
    partial = sum(1 for q in analysis.questions_detected if q.status == "partially_addressed")
    unaddressed = sum(1 for q in analysis.questions_detected if q.status == "unaddressed")

    # Real evidence extraction
    evidence_text = ""
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Questions detected"

    first_q = analysis.questions_detected[0] if analysis.questions_detected else None
    if first_q:
        q_snippet = truncate_text(first_q.question_text, 100)
        user_snippet = extract_user_turn_snippet(session, first_q.turn_number)
        if user_snippet:
            evidence_text = f"Question: \"{q_snippet}\" | Response: \"{user_snippet[0]}\""
            evidence_type = EvidenceType.TRANSCRIPT_EXCERPT.value
            source_ref = user_snippet[1]
        else:
            evidence_text = f"Turn {first_q.turn_number} question: \"{q_snippet}\" — Status: [{first_q.status.replace('_', ' ').capitalize()}]"

    if score >= 85.0:
        what = f"You directly addressed {addressed} of {total_q} questions posed by the AI persona."
        why = "Responses directly answered the specific inquiries without deflecting or skipping requested details."
        impact = "In any interview or meeting, directly answering the question builds immediate credibility and keeps dialogue focused."
        action = "Continue this direct approach: state the core answer first, then add supporting rationale."
    elif score >= 60.0:
        what = f"You addressed most questions ({addressed}/{total_q}), but {partial + unaddressed} question(s) remained only partially answered."
        why = "The response discussed the broader topic but did not provide the specific detail or metric requested by the persona."
        impact = "Unanswered follow-ups leave evaluators uncertain about your depth of experience or decision-making process."
        action = "When asked a follow-up, answer the exact question in your very first sentence before elaborating with context."
    else:
        what = f"Several questions ({unaddressed} unaddressed, {partial} partial out of {total_q}) were not fully resolved."
        why = "Responses shifted into general conversation without answering the persona's specific question."
        impact = "Failing to answer questions can make you appear evasive or unprepared in professional discussions."
        action = "Use the 'Direct Answer First' technique: 1. Give a direct one-sentence answer. 2. Provide one supporting example. 3. Confirm alignment."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence=evidence_text or "; ".join(dim.evidence),
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=(unaddressed > 0)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_communication_fluency(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Generate explainable feedback for Communication & Fluency using objective language signals."""
    if dim.status == DimensionStatus.INSUFFICIENT_EVIDENCE.value:
        return FeedbackItem(
            dimension=dim.name,
            status=dim.status,
            score=None,
            max_score=dim.max_score,
            what="No candidate response turns were available to measure linguistic fluency.",
            why="Communication fluency metrics require speech or text turns.",
            evidence="Analysis observation: 0 user turns recorded.",
            evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
            source_reference="Turn metrics",
            impact="Fluency and structured delivery are fundamental across all practice scenarios.",
            action="Engage in conversation turns to generate measurable delivery signals.",
            priority=FeedbackPriority.LOW.value,
            confidence=EvidenceConfidence.INSUFFICIENT.value,
        )

    score = dim.score
    fillers = analysis.total_filler_count
    filler_pct = analysis.filler_percentage
    reps = len(analysis.repeated_phrases)
    avg_words = analysis.avg_words_per_response

    # Real evidence
    evidence_parts = []
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Speech metrics"

    if fillers > 0:
        top_fillers = list(analysis.filler_word_counts.items())[:3]
        filler_str = ", ".join(f"'{w}' ({c})" for w, c in top_fillers)
        evidence_parts.append(f"Vocal hesitations: {fillers} ({filler_pct:.1f}% of words; {filler_str})")
    else:
        evidence_parts.append("0 filler words detected across candidate turns")

    if analysis.repeated_phrases:
        rep_phrase = analysis.repeated_phrases[0]["phrase"]
        rep_count = analysis.repeated_phrases[0]["count"]
        evidence_parts.append(f"Repeated phrase: '{rep_phrase}' ({rep_count}x)")

    # Check for short snippet
    first_snippet = extract_first_user_snippet(session, 100)
    if first_snippet and fillers > 0:
        evidence_parts.append(f"Sample turn: \"{first_snippet[0]}\"")
        source_ref = first_snippet[1]

    if score >= 85.0:
        what = f"Clean delivery observed with low filler frequency ({fillers} fillers, {filler_pct:.1f}% frequency) and good turn length ({avg_words:.1f} words/turn)."
        why = "Minimal verbal hesitations and varied phrasing kept responses easy to follow."
        impact = "Crisp, fluent delivery projects professional poise and keeps the listener engaged with your content."
        action = "Maintain this steady cadence and continue using deliberate pauses rather than vocal fillers when thinking."
    elif fillers > 4 or filler_pct > 3.0:
        what = f"Language-based confidence indicator: {fillers} filler words detected ({filler_pct:.1f}% of total words)."
        why = "Frequent vocal hesitations interrupt the natural rhythm of your points and dilute message impact."
        impact = "In high-stakes interviews or client pitches, high filler density can distract listeners from your core ideas."
        action = "Practice replacing vocal fillers ('like', 'um', 'you know') with a 1-second silent pause while gathering your next thought."
    elif reps > 0:
        what = f"The transcript contains repetitive phrasing ({reps} repeated transition pattern(s) identified)."
        why = "Reusing identical transition phrases reduces lexical variety across responses."
        impact = "Repetitive sentence starters can make structured answers sound scripted rather than conversational."
        action = "Vary your transitions: instead of repeating transition phrases, transition directly into your evidence."
    else:
        what = f"Responses were brief, averaging {avg_words:.1f} words per response."
        why = "Brief answers leave important context, rationale, and outcomes unspoken."
        impact = "Concise answers are valued, but under-elaborating requires the interviewer to probe for basic details."
        action = "Expand responses by pairing each claim with one concrete rationale or real-world example."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence="; ".join(evidence_parts),
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=(filler_pct > 4.0)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_topic_coverage(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Generate explainable feedback for Scenario Alignment & Topic Coverage."""
    if dim.status == DimensionStatus.NOT_APPLICABLE.value:
        return FeedbackItem(
            dimension=dim.name,
            status=dim.status,
            score=None,
            max_score=dim.max_score,
            what="No specific required topic checklist was configured for this scenario.",
            why="Topic coverage is not evaluated when scenarios are open-ended.",
            evidence="Analysis observation: No expected topic benchmarks configured.",
            evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
            source_reference="Scenario config",
            impact="Open-ended discussions allow flexibility in which topics are highlighted.",
            action="Focus on addressing persona questions directly and staying relevant to the scenario objective.",
            priority=FeedbackPriority.LOW.value,
            confidence=EvidenceConfidence.NOT_APPLICABLE.value,
        )

    score = dim.score
    total_exp = len(analysis.covered_expected_topics) + len(analysis.missing_expected_topics)
    covered = len(analysis.covered_expected_topics)
    missing = analysis.missing_expected_topics

    covered_str = ", ".join(analysis.covered_expected_topics) if analysis.covered_expected_topics else "None"
    missing_str = ", ".join(missing) if missing else "None"

    evidence_text = f"Covered topics: [{covered_str}] | Missing topics: [{missing_str}]"

    if score >= 90.0:
        what = f"You covered {covered} of {total_exp} expected scenario topics ({covered_str})."
        why = "Responses touched on all key subject matter competencies expected in this scenario."
        impact = "Covering all scenario domains demonstrates comprehensive preparation and situational awareness."
        action = "Continue preparing comprehensive talking points for core scenario domains."
    else:
        what = f"You addressed {covered} of {total_exp} expected scenario topics; {len(missing)} topic(s) were not detected: {missing_str}."
        why = "The conversation concluded without addressing essential scenario benchmarks."
        impact = "Missing core topics leaves key evaluator criteria unverified, regardless of how well other topics were answered."
        action = f"Before concluding your responses, actively integrate discussions of: {missing_str}."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence=evidence_text,
        evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
        source_reference="Topic analysis",
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=(len(missing) > 0)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_relevance_substance(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Generate explainable feedback for Relevance & Substance."""
    if dim.status == DimensionStatus.INSUFFICIENT_EVIDENCE.value:
        return FeedbackItem(
            dimension=dim.name,
            status=dim.status,
            score=None,
            max_score=dim.max_score,
            what="No response data available to assess conversational substance.",
            why="Insufficient dialogue turns submitted.",
            evidence="Analysis observation: 0 responses recorded.",
            evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
            source_reference="Turn count",
            impact="Conversational depth requires multi-sentence candidate responses.",
            action="Participate with complete answers to evaluate substance.",
            priority=FeedbackPriority.LOW.value,
            confidence=EvidenceConfidence.INSUFFICIENT.value,
        )

    score = dim.score
    contra_count = len(analysis.potential_contradictions)
    substantive_turns = sum(1 for rf in analysis.response_features if rf.length_category in {"medium", "long"})
    total_turns = len(analysis.response_features)

    evidence_parts = [
        f"{substantive_turns}/{total_turns} turns were substantive (medium or long length)"
    ]
    if contra_count > 0:
        evidence_parts.append(f"Potential contradictions noted: {contra_count}")

    if contra_count > 0:
        what = f"The transcript contains {contra_count} potential contradiction(s) across turns."
        why = "Conflicting statements across turns erode credibility."
        impact = "Inconsistency in factual claims or timelines raises red flags for evaluators and clients."
        action = "Maintain strict factual consistency regarding team sizes, technologies, and project metrics across turns."
    elif score >= 85.0:
        what = f"Strong conversational substance: {substantive_turns} of {total_turns} responses provided thorough explanation."
        why = "Answers were consistently substantive without filler padding or logical discrepancies."
        impact = "Substantive answers provide evaluators with the depth needed to assess your senior-level thinking."
        action = "Maintain this level of depth while ensuring answers remain concise enough for dynamic back-and-forth."
    else:
        what = f"{total_turns - substantive_turns} of {total_turns} responses were brief or lacked supporting detail."
        why = "Single-sentence answers provided minimal technical or contextual substance."
        impact = "Superficial answers make it difficult for interviewers to distinguish between conceptual knowledge and hands-on experience."
        action = "Structure each response with: 1. Core claim. 2. Implementation or practical rationale. 3. Observable result."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence="; ".join(evidence_parts),
        evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
        source_reference="Turn analysis",
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=(contra_count > 0)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_objection_handling(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Generate explainable feedback for Objection Handling."""
    if dim.status == DimensionStatus.NOT_APPLICABLE.value:
        return FeedbackItem(
            dimension=dim.name,
            status=dim.status,
            score=None,
            max_score=dim.max_score,
            what="No explicit objections or pushback statements were voiced by the AI persona in this session.",
            why="Objection handling is only evaluated when the persona raises critical pushback or skepticism.",
            evidence="Analysis observation: 0 persona objections logged.",
            evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
            source_reference="Persona dialogue",
            impact="Responding constructively to skepticism is a decisive skill in executive pitches and senior interviews.",
            action="Practice a scenario with a Skeptical Executive or Critical Interviewer persona to practice handling pushback.",
            priority=FeedbackPriority.LOW.value,
            confidence=EvidenceConfidence.NOT_APPLICABLE.value,
        )

    score = dim.score
    total_obj = len(analysis.objections_evidence)
    addressed = sum(1 for o in analysis.objections_evidence if o.addressed)
    unaddressed = total_obj - addressed

    evidence_items = [
        f"Objection '{o.objection_type}': {'Addressed with evidence' if o.addressed else 'Unaddressed'}"
        for o in analysis.objections_evidence
    ]

    if score >= 90.0:
        what = f"You successfully resolved {addressed} of {total_obj} persona objection(s) with supporting evidence."
        why = "Concerns were acknowledged and countered with factual rationale rather than defensive pushback."
        impact = "Addressing objections calmly and factually transforms skepticism into alignment."
        action = "Continue this structure: acknowledge the stakeholder's concern first, then present mitigating evidence."
    else:
        what = f"{unaddressed} of {total_obj} objection(s) were left unresolved or unmitigated."
        why = "The response did not directly mitigate the persona's voiced pushback."
        impact = "Unresolved objections typically prevent a pitch from advancing or create hesitation in hiring decisions."
        action = "When a persona raises an objection: 1. Acknowledge the validity of their concern. 2. Present direct mitigating evidence. 3. Propose a concrete safeguard or next step."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence="; ".join(evidence_items),
        evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
        source_reference="Objection log",
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=(unaddressed > 0)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


# ==============================================================================
# Mode-Specific Dimension Rules (All 6 Modes)
# ==============================================================================

def explain_hr_star_framework(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """HR Interview: STAR Framework Completeness."""
    if dim.status == DimensionStatus.INSUFFICIENT_EVIDENCE.value:
        return FeedbackItem(
            dimension=dim.name,
            status=dim.status,
            score=None,
            max_score=dim.max_score,
            what="No behavioral responses were available to evaluate STAR framework components.",
            why="Behavioral interview evaluation requires candidate experience stories.",
            evidence="Analysis observation: 0 user messages logged.",
            evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
            source_reference="Turn count",
            impact="HR interviewers specifically assess behavioral structure to evaluate past performance.",
            action="In your next session, provide a structured story from your past experience.",
            priority=FeedbackPriority.LOW.value,
            confidence=EvidenceConfidence.INSUFFICIENT.value,
        )

    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("star_components", {}) if analysis.mode_specific_analysis else {}
    detected = [k for k, v in indicators.items() if v == "detected"]
    missing = [k for k, v in indicators.items() if v != "detected"]

    evidence_text = f"STAR components detected: {', '.join(detected) if detected else 'None'} | Missing: {', '.join(missing) if missing else 'None'}"

    # Try extracting real user snippet containing action or result
    snippet = find_matching_user_snippet(session, ["decided", "implemented", "built", "result", "led"])
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "STAR indicator detector"
    if snippet:
        evidence_text = f"{evidence_text} — Excerpt: \"{snippet[0]}\""
        source_ref = snippet[1]

    if score >= 90.0:
        what = f"Full STAR structure demonstrated: all 4 components (Situation, Task, Action, Result) were articulated."
        why = "You set clear context, identified your personal responsibility, detailed actions taken, and shared the outcome."
        impact = "Complete STAR stories allow HR interviewers to clearly evaluate your individual contribution and problem-solving capability."
        action = "Maintain this structure; ensure your Result component always highlights measurable business or technical outcomes."
    else:
        what = f"Partial STAR structure: detected {len(detected)} of 4 components ({', '.join(detected)}). Missing: {', '.join(missing)}."
        why = f"Your behavioral answers did not explicitly separate {' and '.join(missing)} from general narrative."
        impact = "Missing Action or Result components makes it difficult for recruiters to isolate what YOU accomplished versus the team."
        action = "Structure your response deliberately: 1. Situation (1 sentence). 2. Task (1 sentence). 3. Action (2-3 sentences on what YOU personally did). 4. Result (1 sentence with quantifiable impact)."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence=evidence_text,
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=(len(missing) > 1)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_hr_example_specificity(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """HR Interview: Example Specificity & Outcomes."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators if analysis.mode_specific_analysis else {}
    has_metric = indicators.get("specific_metrics_provided") == "detected"

    evidence_text = "Measurable metrics / timeline details: Detected" if has_metric else "Measurable metrics / timeline details: Not detected"
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Metrics detector"

    if has_metric:
        snippet = find_matching_user_snippet(session, ["%", "$", "days", "weeks", "months", "users", "engineers"])
        if snippet:
            evidence_text = f"{evidence_text} — Excerpt: \"{snippet[0]}\""
            source_ref = snippet[1]

        what = "Your examples included concrete, measurable metrics and timeline outcomes."
        why = "Quantifiable results validate the credibility and scale of your accomplishments."
        impact = "Measurable impact separates average candidates from high-performing candidates in behavioral evaluations."
        action = "Continue backing key accomplishments with quantifiable metrics (percentages, timelines, budget, team scale)."
    else:
        what = "Behavioral examples relied on qualitative statements without specific numbers, percentages, or timelines."
        why = "Phrases like 'significantly improved' or 'team was happy' lack verifiable scale."
        impact = "Without quantifiable outcomes, interviewers cannot gauge the true magnitude of your impact."
        action = "Include at least one measurable data point in every story (e.g., 'reduced turnaround time by 25%', 'mentored 4 engineers', 'delivered 2 weeks early')."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence=evidence_text,
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not has_metric),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_technical_breadth(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Technical Interview: Technical Concept Breadth."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("technical_concepts", {}) if analysis.mode_specific_analysis else {}
    detected = [k for k, v in indicators.items() if v == "detected"]
    missing = [k for k, v in indicators.items() if v != "detected"]

    evidence_text = f"Technical concepts addressed: {', '.join(detected) if detected else 'None'} | Omitted: {', '.join(missing) if missing else 'None'}"

    if score >= 80.0:
        what = f"Strong technical concept breadth: addressed {len(detected)} core technical domains ({', '.join(detected)})."
        why = "Discussion demonstrated solid command across algorithms, data structures, and system design concepts."
        impact = "Broad technical vocabulary and concept linkage demonstrate architectural maturity to engineering interviewers."
        action = "Continue connecting data structure selection directly to algorithmic access patterns and cache efficiency."
    else:
        what = f"Limited technical concept breadth: {len(detected)} domain(s) addressed; {len(missing)} omitted ({', '.join(missing)})."
        why = "Explanations stayed narrow and did not explore related algorithmic or architectural considerations."
        impact = "Technical interviewers look for candidates who proactively discuss trade-offs beyond the immediate code snippet."
        action = "Proactively mention related data structures and design trade-offs (e.g., hash table vs. balanced BST trade-offs)."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence=evidence_text,
        evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
        source_reference="Technical concept detector",
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=(len(missing) > 1)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_technical_complexity(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Technical Interview: Complexity Analysis Rigor."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("technical_concepts", {}) if analysis.mode_specific_analysis else {}
    time_c = indicators.get("Time Complexity") == "detected"
    space_c = indicators.get("Space / Memory Overhead") == "detected"

    evidence_parts = [
        f"Time complexity analysis: {'Detected' if time_c else 'Not detected'}",
        f"Space/memory overhead analysis: {'Detected' if space_c else 'Not detected'}",
    ]

    snippet = find_matching_user_snippet(session, ["o(1)", "o(n)", "o(log", "complexity", "space", "time"])
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Complexity detector"
    if snippet:
        evidence_parts.append(f"Excerpt: \"{snippet[0]}\"")
        source_ref = snippet[1]

    if time_c and space_c:
        what = "You articulated both time complexity and auxiliary space overhead."
        why = "Thorough analysis demonstrated clear understanding of theoretical bounds and runtime memory consumption."
        impact = "Dual complexity analysis is a standard prerequisite in senior engineering interviews."
        action = "Continue explicitly stating both Big-O time and Big-O auxiliary space for every solution proposed."
    elif time_c or space_c:
        what = f"Partial complexity analysis: {'time complexity' if time_c else 'space complexity'} was discussed, but {'space' if time_c else 'time'} was omitted."
        why = "Technical solutions require evaluating both runtime bottlenecks and memory allocation footprints."
        impact = "Ignoring space or time complexity leaves half of the engineering trade-off unanalyzed."
        action = "After explaining the approach, explicitly state time complexity, space complexity, and important edge cases when relevant."
    else:
        what = "No explicit Big-O time or space complexity analysis was detected."
        why = "The approach was described without analyzing algorithmic efficiency or asymptotic bounds."
        impact = "In technical interviews, failing to analyze complexity requires the interviewer to explicitly prompt you, reducing independence marks."
        action = "Immediately conclude your technical solution with: 'In terms of complexity, time is O(...) because ..., and auxiliary space is O(...) due to ...'."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence="; ".join(evidence_parts),
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not (time_c and space_c)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_technical_edge_cases(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Technical Interview: Edge Case & Boundary Reasoning."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("technical_concepts", {}) if analysis.mode_specific_analysis else {}
    edge_c = indicators.get("Edge Cases & Boundary Conditions") == "detected"

    evidence_text = f"Boundary conditions / error handling: {'Detected' if edge_c else 'Not detected'}"
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Edge case detector"

    if edge_c:
        snippet = find_matching_user_snippet(session, ["edge", "boundary", "null", "empty", "concurrency", "overflow"])
        if snippet:
            evidence_text = f"{evidence_text} — Excerpt: \"{snippet[0]}\""
            source_ref = snippet[1]

        what = "You explicitly addressed boundary conditions, empty inputs, or concurrency edge cases."
        why = "Proactive edge case discussion proves production-readiness and defensive programming instincts."
        impact = "Interviewers place high value on candidates who find edge cases without being prompted."
        action = "Continue identifying boundary conditions before writing or finalizing solution logic."
    else:
        what = "No explicit discussion of boundary conditions, empty inputs, or failure modes was detected."
        why = "The response only addressed the happy path without defensive safeguards."
        impact = "Happy-path-only solutions indicate potential fragility in production environments."
        action = "Always list 3 boundary scenarios: 1. Empty/null input. 2. Single-element or extreme scale input. 3. Malformed data or concurrency collisions."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence=evidence_text,
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not edge_c),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_pitch_value_proposition(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Client Pitch: Value Proposition & Business Impact."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("pitch_components", {}) if analysis.mode_specific_analysis else {}
    vp = indicators.get("Value Proposition") == "detected"
    roi = indicators.get("Cost & ROI Justification") == "detected"

    evidence_parts = [
        f"Value proposition articulated: {'Yes' if vp else 'No'}",
        f"Cost/ROI financial justification: {'Yes' if roi else 'No'}",
    ]

    snippet = find_matching_user_snippet(session, ["roi", "cost", "value", "revenue", "savings", "efficiency"])
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Pitch component detector"
    if snippet:
        evidence_parts.append(f"Excerpt: \"{snippet[0]}\"")
        source_ref = snippet[1]

    if vp and roi:
        what = "Clearly articulated both the customer value proposition and financial return on investment (ROI)."
        why = "Connected solution capabilities directly to client business gains and financial payback."
        impact = "Executive buyers require clear ROI models to justify expenditure to their board and finance committees."
        action = "Maintain this commercial clarity: tie technical capabilities directly to cost reduction or revenue enhancement."
    elif vp:
        what = "Customer value proposition was articulated, but financial ROI / cost justification was missing."
        why = "The pitch explained why the product is helpful but did not explain why it makes financial sense."
        impact = "Without quantifiable financial benefits, decision-makers cannot build an internal business case."
        action = "Always pair value propositions with a financial metric (e.g., 'expected payback within 6 months through a 20% reduction in licensing costs')."
    else:
        what = "Core customer value proposition and financial return were not clearly articulated."
        why = "Pitch focused on technical features rather than business problems and measurable client outcomes."
        impact = "Feature-centric pitches lose executive interest and fail to differentiate from competitors."
        action = "Lead with the client's problem, present the solution as the answer, and substantiate with a clear ROI metric."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence="; ".join(evidence_parts),
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not (vp and roi)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_pitch_security_scalability(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Client Pitch: Enterprise Security & Scalability."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("pitch_components", {}) if analysis.mode_specific_analysis else {}
    sec = indicators.get("Security & Compliance") == "detected"
    scale = indicators.get("Scalability & Performance") == "detected"

    evidence_parts = [
        f"Security/compliance safeguards: {'Detected' if sec else 'Not detected'}",
        f"Scalability/SLA guarantees: {'Detected' if scale else 'Not detected'}",
    ]

    snippet = find_matching_user_snippet(session, ["security", "compliance", "soc2", "gdpr", "sla", "scale"])
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Security detector"
    if snippet:
        evidence_parts.append(f"Excerpt: \"{snippet[0]}\"")
        source_ref = snippet[1]

    if sec and scale:
        what = "Addressed enterprise non-functional requirements including security safeguards, compliance, and scalability."
        why = "Proactively answered critical vendor qualification criteria."
        impact = "Enterprise deals routinely stall in security and legal reviews; proactive coverage accelerates procurement."
        action = "Continue proactively addressing compliance certifications (SOC 2, GDPR) and uptime SLAs in pitches."
    else:
        missing_elem = "security safeguards" if not sec else "scalability and SLA guarantees"
        what = f"Enterprise readiness gap: {missing_elem} were not covered in candidate pitch responses."
        why = "B2B buyers cannot commit without clear data protection and uptime assurances."
        impact = "Leaving out security or scalability triggers objections from IT, legal, and compliance stakeholders."
        action = "Include a dedicated 30-second slide or talking point on enterprise data encryption, compliance certifications, and SLA guarantees."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence="; ".join(evidence_parts),
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not (sec and scale)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_viva_architecture_stack(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Project Viva: Architecture & Stack Justification."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("viva_components", {}) if analysis.mode_specific_analysis else {}
    arch = indicators.get("Architecture & Design Justification") == "detected"
    stack = indicators.get("Technology Stack Rationale") == "detected"

    evidence_parts = [
        f"Architecture design patterns: {'Detected' if arch else 'Not detected'}",
        f"Technology trade-off rationale: {'Detected' if stack else 'Not detected'}",
    ]

    snippet = find_matching_user_snippet(session, ["architecture", "chose", "framework", "database", "rationale", "pattern"])
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Viva architecture detector"
    if snippet:
        evidence_parts.append(f"Excerpt: \"{snippet[0]}\"")
        source_ref = snippet[1]

    if arch and stack:
        what = "Defended system architecture choices and provided explicit rationale for tech stack trade-offs."
        why = "Demonstrated that technology choices were deliberate engineering decisions rather than default choices."
        impact = "Academic and viva examiners test whether the candidate designed the system with architectural intent."
        action = "Continue connecting the architecture choice to the problem it solves instead of only listing technologies."
    else:
        what = "System architecture and technology stack justifications were incomplete or descriptive rather than analytical."
        why = "Technologies were mentioned without explaining why alternatives were rejected."
        impact = "Examiners may conclude the tech stack was chosen arbitrarily without evaluating engineering trade-offs."
        action = "When explaining your project, connect the architecture choice to the problem it solves instead of only listing technologies."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence="; ".join(evidence_parts),
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not (arch and stack)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_viva_methodology_validation(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Project Viva: Methodology & Validation Rigor."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("viva_components", {}) if analysis.mode_specific_analysis else {}
    meth = indicators.get("Methodology & Experimental Rigor") == "detected"

    evidence_text = f"Experimental validation metrics/baseline: {'Detected' if meth else 'Not detected'}"
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Validation detector"

    if meth:
        snippet = find_matching_user_snippet(session, ["baseline", "metric", "accuracy", "latency", "evaluation", "tested"])
        if snippet:
            evidence_text = f"{evidence_text} — Excerpt: \"{snippet[0]}\""
            source_ref = snippet[1]

        what = "Explained experimental methodology, evaluation metrics, and validation baselines."
        why = "Grounded system performance claims in measurable empirical data."
        impact = "Empirical validation is the core requirement of any academic defense or scientific project viva."
        action = "Maintain clear documentation of test benchmarks, baselines, and statistical validation metrics."
    else:
        what = "Experimental validation was limited; quantitative baselines and evaluation metrics were not detected."
        why = "System outcomes were stated qualitatively without benchmark comparisons."
        impact = "Unsubstantiated performance claims are quickly challenged during academic defenses."
        action = "Cite concrete validation methods: 1. Baseline used for comparison. 2. Specific evaluation metrics (F1, latency, throughput). 3. Test dataset size."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence=evidence_text,
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not meth),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_viva_limitations(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Project Viva: Awareness of Limitations & Constraints."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("viva_components", {}) if analysis.mode_specific_analysis else {}
    lim = indicators.get("Awareness of Limitations") == "detected"

    evidence_text = f"System limitations / future work acknowledged: {'Yes' if lim else 'No'}"
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Limitations detector"

    if lim:
        snippet = find_matching_user_snippet(session, ["limitation", "constraint", "bottleneck", "future work", "tradeoff"])
        if snippet:
            evidence_text = f"{evidence_text} — Excerpt: \"{snippet[0]}\""
            source_ref = snippet[1]

        what = "Demonstrated honest academic appraisal of project constraints and outlined future work."
        why = "Acknowledging technical boundaries indicates genuine domain depth and intellectual maturity."
        impact = "Viva panels respect candidates who understand the boundaries of their solution rather than claiming perfection."
        action = "Continue framing limitations positively as opportunities for future architectural enhancements."
    else:
        what = "Did not explicitly acknowledge architectural bottlenecks, data constraints, or system limitations."
        why = "The project was presented without recognizing practical trade-offs or constraints."
        impact = "Failing to acknowledge obvious constraints can make a candidate appear unaware of production realities."
        action = "Identify 2-3 genuine constraints in your project (e.g., memory scaling, cold start latency) and present proposed mitigations."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence=evidence_text,
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not lim),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_gd_argument_quality(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Group Discussion: Argument Quality & Evidence."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("discussion_dynamics", {}) if analysis.mode_specific_analysis else {}
    evi = indicators.get("Evidence-Backed Reasoning") == "detected"
    counter = indicators.get("Respectful Counter-Argument / Nuance") == "detected"

    evidence_parts = [
        f"Evidence-backed data points: {'Detected' if evi else 'Not detected'}",
        f"Nuanced counter-arguments: {'Detected' if counter else 'Not detected'}",
    ]

    snippet = find_matching_user_snippet(session, ["evidence", "data", "counter", "on the other hand", "perspective"])
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Discussion detector"
    if snippet:
        evidence_parts.append(f"Excerpt: \"{snippet[0]}\"")
        source_ref = snippet[1]

    if evi and counter:
        what = "Provided evidence-backed arguments and incorporated nuanced, multi-sided perspectives."
        why = "Arguments were supported with factual examples rather than subjective assertions."
        impact = "Group discussion evaluators look for candidates who elevate dialogue through substantive reasoning."
        action = "Continue anchoring points with verifiable facts, industry case studies, or logical deductions."
    else:
        what = "Arguments were primarily opinion-based with limited empirical evidence or multi-perspective counter-points."
        why = "Points were stated without corroborating data, case studies, or acknowledgment of alternative viewpoints."
        impact = "Unsubstantiated opinions are easily disputed in collaborative discussions."
        action = "Use the 'Point → Evidence → Counter-point' structure: state your view, provide a supporting fact, then acknowledge an opposing nuance."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence="; ".join(evidence_parts),
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not (evi and counter)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_gd_synthesis_dynamics(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Group Discussion: Synthesis & Collaborative Dynamics."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("discussion_dynamics", {}) if analysis.mode_specific_analysis else {}
    agree = indicators.get("Constructive Agreement / Building On Ideas") == "detected"
    synth = indicators.get("Synthesis / Common Ground") == "detected"

    evidence_parts = [
        f"Building on others' ideas: {'Detected' if agree else 'Not detected'}",
        f"Synthesizing consensus: {'Detected' if synth else 'Not detected'}",
    ]

    snippet = find_matching_user_snippet(session, ["agree", "building on", "common ground", "synthesizing", "summarize"])
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Synthesis detector"
    if snippet:
        evidence_parts.append(f"Excerpt: \"{snippet[0]}\"")
        source_ref = snippet[1]

    if agree and synth:
        what = "Demonstrated collaborative leadership by acknowledging peers' points and synthesizing common ground."
        why = "Bridged disparate points into an actionable group consensus."
        impact = "Moderators highly reward candidates who facilitate group alignment rather than competing for airtime."
        action = "Continue summarizing the group's emerging consensus at critical decision junctures."
    else:
        what = "Dialogue showed limited synthesis of other participants' arguments or efforts to build common ground."
        why = "Contributions functioned as isolated statements rather than connecting to peer inputs."
        impact = "Candidates who do not build on others risk being seen as self-focused rather than team players."
        action = "Start contributions by acknowledging a peer: 'Building on what [Name] said about X, we should also consider Y to reach consensus on Z'."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence="; ".join(evidence_parts),
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not (agree or synth)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_managerial_empathy(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Managerial Interview: Leadership Empathy & Coaching."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("leadership_signals", {}) if analysis.mode_specific_analysis else {}
    emp = indicators.get("Empathetic Leadership & 1-on-1 Communication") == "detected"

    evidence_text = f"1-on-1 communication / empathy: {'Detected' if emp else 'Not detected'}"
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Empathy detector"

    if emp:
        snippet = find_matching_user_snippet(session, ["1-on-1", "coach", "listen", "support", "empathy", "career"])
        if snippet:
            evidence_text = f"{evidence_text} — Excerpt: \"{snippet[0]}\""
            source_ref = snippet[1]

        what = "Demonstrated empathetic people leadership, active listening, and structured 1-on-1 coaching approaches."
        why = "Balanced business deliverables with team member well-being and professional growth."
        impact = "Modern engineering leadership relies on psychological safety and coaching to retain top talent."
        action = "Continue framing performance conversations around collaborative inquiry and growth plans."
    else:
        what = "Responses focused on operational tasks rather than people leadership, active listening, or 1-on-1 coaching."
        why = "Addressed team challenges mechanically without articulating empathetic communication practices."
        impact = "Managerial interviewers look for leaders who develop people, not just assign tickets."
        action = "Outline your 1-on-1 coaching framework: 1. Listen without interrupting. 2. Understand root causes. 3. Co-create an actionable growth plan."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence=evidence_text,
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not emp),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_managerial_conflict(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Managerial Interview: Conflict Mediation & De-escalation."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("leadership_signals", {}) if analysis.mode_specific_analysis else {}
    conf = indicators.get("Conflict Mediation & De-escalation") == "detected"

    evidence_text = f"Conflict de-escalation / mediation: {'Detected' if conf else 'Not detected'}"
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Conflict detector"

    if conf:
        snippet = find_matching_user_snippet(session, ["conflict", "mediate", "disagree", "alignment", "resolve"])
        if snippet:
            evidence_text = f"{evidence_text} — Excerpt: \"{snippet[0]}\""
            source_ref = snippet[1]

        what = "Articulated clear steps to mediate engineering disagreements and restore team alignment."
        why = "De-escalated tension by focusing on shared business objectives and objective data."
        impact = "Executive teams require leaders who resolve friction early before it damages culture or velocity."
        action = "Continue utilizing data-driven mediation and 'disagree and commit' frameworks."
    else:
        what = "Described limited frameworks for resolving interpersonal or technical conflict among team members."
        why = "Did not detail a structured conflict resolution or mediation process."
        impact = "Unresolved conflict leads to team fragmentation and missed delivery milestones."
        action = "Adopt a 3-step conflict framework: 1. Separate people from the problem. 2. Anchor on shared customer outcomes. 3. Establish clear consensus or leadership decision rules."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence=evidence_text,
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not conf),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


def explain_managerial_prioritization(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """Managerial Interview: Prioritization & Ownership."""
    score = dim.score
    indicators = analysis.mode_specific_analysis.indicators.get("leadership_signals", {}) if analysis.mode_specific_analysis else {}
    prio = indicators.get("Prioritization Frameworks") == "detected"
    own = indicators.get("Ownership & Accountability") == "detected"

    evidence_parts = [
        f"Prioritization frameworks: {'Detected' if prio else 'Not detected'}",
        f"Personal ownership & accountability: {'Detected' if own else 'Not detected'}",
    ]

    snippet = find_matching_user_snippet(session, ["priority", "prioritize", "ownership", "responsible", "trade-off", "rice"])
    evidence_type = EvidenceType.ANALYSIS_OBSERVATION.value
    source_ref = "Prioritization detector"
    if snippet:
        evidence_parts.append(f"Excerpt: \"{snippet[0]}\"")
        source_ref = snippet[1]

    if prio and own:
        what = "Demonstrated structured prioritization frameworks while taking personal accountability for outcomes."
        why = "Exhibited clear decision-making criteria under resource constraints without deflecting blame."
        impact = "Accountable leaders who can prioritize under pressure build high-trust organizations."
        action = "Continue referencing structured prioritization models (e.g. RICE, impact vs. effort matrices) during roadmap discussions."
    else:
        what = "Prioritization criteria or personal ownership were only partially articulated."
        why = "Decisions were explained without clear framework-driven rationale."
        impact = "Lack of structured prioritization leads to reactive execution and team burnout."
        action = "Reference explicit prioritization criteria (e.g., customer impact, engineering effort, strategic urgency) when explaining roadmap trade-offs."

    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=what,
        why=why,
        evidence="; ".join(evidence_parts),
        evidence_type=evidence_type,
        source_reference=source_ref,
        impact=impact,
        action=action,
        priority=_determine_priority(score, has_critical_gap=not (prio and own)),
        confidence=EvidenceConfidence.SUFFICIENT.value,
    )


# ==============================================================================
# Master Rule Dispatcher
# ==============================================================================

DIMENSION_RULE_DISPATCHER = {
    # Common
    "Question Handling": explain_question_handling,
    "Communication & Fluency": explain_communication_fluency,
    "Scenario Alignment & Topic Coverage": explain_topic_coverage,
    "Relevance & Substance": explain_relevance_substance,
    "Objection Handling": explain_objection_handling,
    # HR Interview
    "STAR Framework Completeness": explain_hr_star_framework,
    "Example Specificity & Outcomes": explain_hr_example_specificity,
    # Technical Interview
    "Technical Concept Breadth": explain_technical_breadth,
    "Complexity Analysis Rigor": explain_technical_complexity,
    "Edge Case & Boundary Reasoning": explain_technical_edge_cases,
    # Client Pitch
    "Value Proposition & Business Impact": explain_pitch_value_proposition,
    "Enterprise Security & Scalability": explain_pitch_security_scalability,
    # Project Viva
    "Architecture & Stack Justification": explain_viva_architecture_stack,
    "Methodology & Validation Rigor": explain_viva_methodology_validation,
    "Awareness of Limitations": explain_viva_limitations,
    # Group Discussion
    "Argument Quality & Evidence": explain_gd_argument_quality,
    "Synthesis & Collaborative Dynamics": explain_gd_synthesis_dynamics,
    # Managerial Interview
    "Leadership Empathy & Coaching": explain_managerial_empathy,
    "Conflict Mediation & De-escalation": explain_managerial_conflict,
    "Prioritization & Ownership": explain_managerial_prioritization,
}


def explain_dimension(
    dim: ScoreDimension,
    analysis: ConversationAnalysis,
    session: Optional[PracticeSession] = None
) -> FeedbackItem:
    """
    Generate an explainable FeedbackItem for any evaluated or non-applicable dimension.
    """
    handler = DIMENSION_RULE_DISPATCHER.get(dim.name)
    if handler:
        return handler(dim, analysis, session)

    # Generic Fallback Handler for any unmapped or dynamic dimension
    evidence_str = "; ".join(dim.evidence) if dim.evidence else "No specific evidence logged."
    score = dim.score if dim.is_evaluated() else None
    
    return FeedbackItem(
        dimension=dim.name,
        status=dim.status,
        score=score,
        max_score=dim.max_score,
        what=f"Observation for {dim.name}: {dim.rationale}",
        why=f"This influenced the score based on: {dim.rationale}",
        evidence=evidence_str,
        evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
        source_reference="Dimension evaluation",
        impact=f"Performance in {dim.name} directly impacts overall scenario effectiveness.",
        action="Review the evidence items and apply structured practices during your next turn.",
        priority=_determine_priority(score),
        confidence=EvidenceConfidence.SUFFICIENT.value if dim.is_evaluated() else EvidenceConfidence.INSUFFICIENT.value,
    )
