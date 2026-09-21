"""
Comprehensive test suite for Phase 6: Explainable Feedback Engine.
Covers models, real evidence preservation, explainability framework,
all 6 modes, determinism, edge cases, and language safety.
"""

import pytest
from typing import List

from src.scenarios.scenario_models import Scenario, Persona
from src.conversation.conversation_models import (
    PracticeSession,
    ConversationMessage,
    MessageRole,
    SessionStatus,
)
from src.intelligence.analysis_models import (
    ConversationAnalysis,
    ResponseFeature,
    QuestionEvidence,
    ConcernEvidence,
    ObjectionEvidence,
    ModeSpecificEvidence,
)
from src.evaluation.evaluation_models import (
    EvaluationResult,
    ScoreDimension,
    ModeEvaluation,
    DimensionStatus,
)
from src.evaluation.evaluation_engine import EvaluationEngine
from src.intelligence.conversation_analyzer import ConversationAnalyzer
from src.feedback.feedback_models import (
    FeedbackPriority,
    EvidenceType,
    EvidenceConfidence,
    FeedbackItem,
    StrengthFeedbackItem,
    ImprovementFeedbackItem,
    PracticeAction,
    FeedbackResult,
)
from src.feedback.evidence_utils import (
    truncate_text,
    extract_user_turn_snippet,
    find_matching_user_snippet,
    extract_first_user_snippet,
    format_evidence_display,
)
from src.feedback.feedback_rules import (
    explain_dimension,
    explain_question_handling,
    explain_communication_fluency,
    explain_topic_coverage,
    explain_relevance_substance,
    explain_objection_handling,
)
from src.feedback.feedback_engine import FeedbackEngine


# ==============================================================================
# 1. Model Tests
# ==============================================================================

def test_feedback_item_valid():
    """Verify that FeedbackItem validates required fields and serializes to dict."""
    item = FeedbackItem(
        dimension="Question Handling",
        status="evaluated",
        what="You answered 2 of 2 questions directly.",
        why="Responses were relevant and addressed each prompt.",
        evidence="Analysis observation: 2 questions addressed.",
        impact="Direct answers build credibility with interviewers.",
        action="Continue answering the core question first.",
        score=90.0,
        max_score=100.0,
        evidence_type="Analysis observation",
        source_reference="Turn 1-2",
        priority="Low Priority",
        confidence="sufficient",
    )
    assert item.dimension == "Question Handling"
    assert item.is_evaluated() is True
    d = item.to_dict()
    assert d["dimension"] == "Question Handling"
    assert d["score"] == 90.0
    assert d["priority"] == "Low Priority"
    assert d["what"] == "You answered 2 of 2 questions directly."


def test_feedback_item_validation_errors():
    """Verify that FeedbackItem catches invalid score bounds or missing fields."""
    with pytest.raises(ValueError):
        FeedbackItem(
            dimension="",
            status="evaluated",
            what="What",
            why="Why",
            evidence="Evi",
            impact="Imp",
            action="Act",
        )

    with pytest.raises(ValueError):
        FeedbackItem(
            dimension="Test",
            status="evaluated",
            what="What",
            why="Why",
            evidence="Evi",
            impact="Imp",
            action="Act",
            score=110.0,  # exceeds max_score
            max_score=100.0,
        )


def test_strength_and_improvement_models():
    """Verify StrengthFeedbackItem, ImprovementFeedbackItem, and PracticeAction."""
    strength = StrengthFeedbackItem(
        title="Direct Responses",
        what="Answered inquiries promptly.",
        evidence="Transcript excerpt: 'We deployed to AWS.'",
        impact="Builds trust.",
        evidence_type="Transcript excerpt",
        source_reference="Turn 1",
    )
    assert strength.title == "Direct Responses"
    sd = strength.to_dict()
    assert sd["evidence_type"] == "Transcript excerpt"

    improvement = ImprovementFeedbackItem(
        title="Time Complexity Rigor",
        what="Omitted space complexity.",
        why="Technical interviews require dual complexity analysis.",
        evidence="Analysis observation: Space complexity not detected.",
        impact="Leaves design incomplete.",
        action="Explicitly state both time and space complexity.",
        priority="High Priority",
    )
    assert improvement.priority == "High Priority"
    idict = improvement.to_dict()
    assert idict["action"] == "Explicitly state both time and space complexity."

    action = PracticeAction(
        title="Complexity Rigor",
        action="State O(N) space explicitly.",
        scenario_context="Technical Interview",
        priority="High Priority",
    )
    assert action.scenario_context == "Technical Interview"
    assert action.to_dict()["priority"] == "High Priority"


def test_feedback_result_model():
    """Verify FeedbackResult model structure and serialization."""
    res = FeedbackResult(
        session_id="sess-123",
        mode="HR Interview",
        difficulty="Intermediate",
        overall_summary="Strong performance.",
        items=[],
        strengths=[],
        improvements=[],
        priority_actions=[],
        insufficient_evidence_notes=[],
    )
    assert res.session_id == "sess-123"
    rd = res.to_dict()
    assert rd["mode"] == "HR Interview"
    assert isinstance(rd["items"], list)


# ==============================================================================
# 2. Evidence Utilities & Real Evidence Integrity Tests
# ==============================================================================

def test_evidence_utils_truncation():
    """Verify safe truncation preserves word boundaries."""
    text = "The quick brown fox jumps over the lazy dog in the sunny morning."
    truncated = truncate_text(text, max_chars=30)
    assert len(truncated) <= 33  # text + '...'
    assert truncated.endswith("...")
    assert "quick" in truncated


def test_evidence_utils_transcript_extraction():
    """Verify real transcript excerpts are extracted from PracticeSession."""
    session = PracticeSession(session_id="s1", mode="HR Interview")
    session.add_message(MessageRole.ASSISTANT.value, "Can you tell me about a time you handled conflict?")
    session.add_message(
        MessageRole.USER.value,
        "In my previous role as lead engineer, two senior developers disagreed on GraphQL vs REST. I organized a prototype benchmark and we aligned on REST."
    )

    snippet = extract_user_turn_snippet(session, turn_num=1)
    assert snippet is not None
    assert "In my previous role" in snippet[0]
    assert snippet[1] == "Turn 1"

    # Non-existent turn returns None
    assert extract_user_turn_snippet(session, turn_num=99) is None

    # Keyword search
    kw_snippet = find_matching_user_snippet(session, ["GraphQL", "REST"])
    assert kw_snippet is not None
    assert "GraphQL" in kw_snippet[0]
    assert kw_snippet[1] == "Turn 1"


def test_evidence_formatting_attribution():
    """Verify evidence attribution formatting clearly states evidence type."""
    fmt = format_evidence_display("Candidate answered question", evidence_type="Analysis observation")
    assert fmt.startswith("[Analysis observation]:")

    fmt_quote = format_evidence_display("I reduced latency by 30%", evidence_type="Transcript excerpt", source_reference="Turn 2")
    assert "[Transcript excerpt — Turn 2]: \"I reduced latency by 30%\"" == fmt_quote

    # Derived metric/observation must be labeled [Analysis observation] without turn/detector suffix
    fmt_derived = format_evidence_display(
        "Time complexity analysis: Detected; Space/memory overhead analysis: Detected",
        evidence_type="Analysis observation",
        source_reference="Complexity detector",
    )
    assert fmt_derived == "[Analysis observation]: Time complexity analysis: Detected; Space/memory overhead analysis: Detected"

    # Analysis observations must never be presented as transcript excerpts
    fmt_safe = format_evidence_display(
        "Time complexity analysis: Detected; Space/memory overhead analysis: Detected",
        evidence_type="Transcript excerpt",
        source_reference="Turn 1",
    )
    assert fmt_safe.startswith("[Analysis observation]:")
    assert "Transcript excerpt" not in fmt_safe


def test_evidence_labeling_consistency():
    """Verify evidence labeling distinguishes exact user words from derived metrics/observations."""
    # 1. Exact user transcript words -> [Transcript excerpt — Turn X]
    exact_words = "We migrated the monolith to microservices and cut p99 latency by 45%."
    formatted_quote = format_evidence_display(
        exact_words,
        evidence_type=EvidenceType.TRANSCRIPT_EXCERPT.value,
        source_reference="Turn 3",
    )
    assert formatted_quote == f'[Transcript excerpt — Turn 3]: "{exact_words}"'

    # 2. Derived metric/observation -> [Analysis observation]
    derived_metric = "Time complexity analysis: Detected; Space/memory overhead analysis: Detected"
    formatted_metric = format_evidence_display(
        derived_metric,
        evidence_type=EvidenceType.ANALYSIS_OBSERVATION.value,
        source_reference="Complexity detector",
    )
    assert formatted_metric == f"[Analysis observation]: {derived_metric}"

    # 3. Guard against mislabeling derived metric as transcript excerpt
    mislabeled = format_evidence_display(
        derived_metric,
        evidence_type=EvidenceType.TRANSCRIPT_EXCERPT.value,
        source_reference="Turn 1",
    )
    assert mislabeled == f"[Analysis observation]: {derived_metric}"
    assert "Transcript excerpt" not in mislabeled


# ==============================================================================
# 3. Explainability & Feedback Engine Integration Tests
# ==============================================================================

@pytest.fixture
def sample_hr_session() -> PracticeSession:
    """Fixture providing a realistic HR interview session."""
    session = PracticeSession(
        session_id="hr-sess-1",
        scenario_id="hr_behavioral_01",
        mode="HR Interview",
        difficulty="Intermediate",
    )
    session.add_message(MessageRole.ASSISTANT.value, "Tell me about a challenging technical deadline you faced.")
    session.add_message(
        MessageRole.USER.value,
        "In my previous role, our team faced a tight 3-week deadline to deliver a payment service. "
        "As tech lead, I took the initiative to simplify the architecture and prioritized core payment routes. "
        "We successfully launched on time with zero downtime and reduced payment processing latency by 35%."
    )
    session.turn_number = 1
    session.status = SessionStatus.COMPLETED.value
    return session


def test_feedback_engine_hr_session(sample_hr_session):
    """Verify complete feedback generation for HR Interview with STAR components."""
    analyzer = ConversationAnalyzer()
    scenario = Scenario(
        id="hr_behavioral_01",
        name="HR Behavioral",
        mode="HR Interview",
        description="Behavioral questions.",
        difficulty="Intermediate",
        persona="Lead Recruiter",
        objective="Assess STAR method.",
        expected_topics=["Leadership", "Deadline Management"],
        opening_message="Welcome!",
        max_turns=3,
    )
    persona = Persona(
        id="recruiter_1",
        name="Sarah Recruiter",
        role="Recruiter",
        personality="Direct and observant",
        background="Senior Talent Acquisition",
        objective="Evaluate STAR competency",
        knowledge_level="Expert",
        communication_style="Professional",
        concerns=["Communication", "Collaboration"],
    )

    analysis = analyzer.analyze(sample_hr_session, scenario, persona)
    eval_engine = EvaluationEngine()
    evaluation = eval_engine.evaluate(analysis, scenario, persona)

    feedback_engine = FeedbackEngine()
    feedback = feedback_engine.generate_feedback(analysis, evaluation, sample_hr_session, scenario, persona)

    assert isinstance(feedback, FeedbackResult)
    assert feedback.session_id == sample_hr_session.session_id
    assert feedback.mode == "HR Interview"
    assert len(feedback.items) > 0

    # Verify every evaluated item has WHAT, WHY, EVIDENCE, IMPACT, ACTION
    for item in feedback.items:
        assert item.what, f"Missing WHAT in {item.dimension}"
        assert item.why, f"Missing WHY in {item.dimension}"
        assert item.impact, f"Missing IMPACT in {item.dimension}"
        assert item.action, f"Missing ACTION in {item.dimension}"
        assert item.evidence, f"Missing EVIDENCE in {item.dimension}"

    # Verify evidence-backed strengths
    assert len(feedback.strengths) > 0
    for s in feedback.strengths:
        assert s.what
        assert s.evidence
        assert s.impact

    # Verify priority actions
    assert len(feedback.priority_actions) > 0
    for pa in feedback.priority_actions:
        assert pa.title
        assert pa.action
        assert pa.scenario_context


# ==============================================================================
# 4. Mode-Specific Feedback Tests (All 6 Modes)
# ==============================================================================

def test_feedback_technical_interview():
    """Verify Technical Interview feedback covers complexity analysis and edge cases."""
    session = PracticeSession(session_id="tech-1", mode="Technical Interview")
    session.add_message(MessageRole.ASSISTANT.value, "How would you design an LRU Cache?")
    session.add_message(
        MessageRole.USER.value,
        "I would use a doubly linked list combined with a hash map. "
        "The hash map provides O(1) lookup time, while the doubly linked list allows O(1) eviction and insertion. "
        "The auxiliary space complexity is O(capacity) for storing node references. "
        "For edge cases, I handle capacity equal to zero and null key updates gracefully."
    )
    session.turn_number = 1

    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session)
    eval_engine = EvaluationEngine()
    evaluation = eval_engine.evaluate(analysis)

    feedback_engine = FeedbackEngine()
    feedback = feedback_engine.generate_feedback(analysis, evaluation, session)

    item_dims = {item.dimension: item for item in feedback.items}
    assert "Complexity Analysis Rigor" in item_dims
    assert "Edge Case & Boundary Reasoning" in item_dims

    comp_item = item_dims["Complexity Analysis Rigor"]
    assert "time complexity" in comp_item.what.lower() or "complexity" in comp_item.what.lower()
    assert comp_item.is_evaluated() is True


def test_feedback_client_pitch():
    """Verify Client Pitch feedback covers value proposition, ROI, and security."""
    session = PracticeSession(session_id="pitch-1", mode="Client Pitch")
    session.add_message(MessageRole.ASSISTANT.value, "Why should our enterprise adopt your analytics platform?")
    session.add_message(
        MessageRole.USER.value,
        "Our platform provides real-time customer behavioral intelligence that delivers immediate business value. "
        "Clients typically achieve positive cost ROI within four months by reducing customer churn by 18%. "
        "From an enterprise security perspective, all data is encrypted at rest with SOC2 Type II compliance and guaranteed 99.99% uptime SLA."
    )
    session.turn_number = 1

    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session)
    evaluation = EvaluationEngine().evaluate(analysis)

    feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)
    item_dims = {item.dimension: item for item in feedback.items}

    assert "Value Proposition & Business Impact" in item_dims
    assert "Enterprise Security & Scalability" in item_dims
    vp_item = item_dims["Value Proposition & Business Impact"]
    assert "return on investment" in vp_item.what.lower() or "value proposition" in vp_item.what.lower()


def test_feedback_project_viva():
    """Verify Project Viva feedback covers architecture, methodology, and limitations."""
    session = PracticeSession(session_id="viva-1", mode="Project Viva")
    session.add_message(MessageRole.ASSISTANT.value, "Defend your architectural choices and experimental validation.")
    session.add_message(
        MessageRole.USER.value,
        "We chose a microservices architecture using gRPC because our system required sub-millisecond inter-service communication. "
        "For experimental validation, we evaluated performance against a baseline monolithic system using an F1 metric on 50,000 synthetic requests. "
        "One key limitation of our design is cold-start latency in serverless worker nodes, which we plan to address in future work with provisioned concurrency."
    )
    session.turn_number = 1

    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session)
    evaluation = EvaluationEngine().evaluate(analysis)

    feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)
    item_dims = {item.dimension: item for item in feedback.items}

    assert "Architecture & Stack Justification" in item_dims
    assert "Methodology & Validation Rigor" in item_dims
    assert "Awareness of Limitations" in item_dims


def test_feedback_group_discussion():
    """Verify Group Discussion feedback covers collaborative dynamics and argument quality."""
    session = PracticeSession(session_id="gd-1", mode="Group Discussion")
    session.add_message(MessageRole.ASSISTANT.value, "Should AI regulation be centralized or decentralized?")
    session.add_message(
        MessageRole.USER.value,
        "I agree with the point made earlier regarding risk mitigation. "
        "Building on what was discussed, empirical evidence from financial sector compliance shows that centralized oversight prevents regulatory fragmentation. "
        "However, on the other hand, rapid innovation requires local agility. "
        "To synthesize common ground, a tiered framework with centralized high-risk auditing and local sandbox testing is ideal."
    )
    session.turn_number = 1

    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session)
    evaluation = EvaluationEngine().evaluate(analysis)

    feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)
    item_dims = {item.dimension: item for item in feedback.items}

    assert "Argument Quality & Evidence" in item_dims
    assert "Synthesis & Collaborative Dynamics" in item_dims
    synth_item = item_dims["Synthesis & Collaborative Dynamics"]
    assert "synthesis" in synth_item.what.lower() or "collaborative" in synth_item.what.lower()


def test_feedback_managerial_interview():
    """Verify Managerial Interview feedback covers empathy, coaching, conflict, and prioritization."""
    session = PracticeSession(session_id="mgr-1", mode="Managerial Interview")
    session.add_message(MessageRole.ASSISTANT.value, "How do you handle underperforming engineers and team friction?")
    session.add_message(
        MessageRole.USER.value,
        "In our 1-on-1 coaching conversations, I prioritize active listening to understand personal root causes and support career growth with empathy. "
        "When technical conflict arises, I mediate the disagreement by de-escalating emotions and focusing on shared team deliverables. "
        "For roadmap planning, I use the RICE prioritization framework and maintain personal ownership and accountability for delivery milestones."
    )
    session.turn_number = 1

    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session)
    evaluation = EvaluationEngine().evaluate(analysis)

    feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)
    item_dims = {item.dimension: item for item in feedback.items}

    assert "Leadership Empathy & Coaching" in item_dims
    assert "Conflict Mediation & De-escalation" in item_dims
    assert "Prioritization & Ownership" in item_dims


# ==============================================================================
# 5. Determinism Tests
# ==============================================================================

def test_feedback_engine_determinism(sample_hr_session):
    """Verify that multiple runs with identical inputs produce identical feedback results."""
    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(sample_hr_session)
    evaluation = EvaluationEngine().evaluate(analysis)

    feedback_engine = FeedbackEngine()
    fb1 = feedback_engine.generate_feedback(analysis, evaluation, sample_hr_session)
    fb2 = feedback_engine.generate_feedback(analysis, evaluation, sample_hr_session)

    assert fb1.to_dict() == fb2.to_dict()
    assert len(fb1.items) == len(fb2.items)
    for i in range(len(fb1.items)):
        assert fb1.items[i].to_dict() == fb2.items[i].to_dict()


# ==============================================================================
# 6. Edge Cases & Insufficient Evidence Tests
# ==============================================================================

def test_empty_conversation():
    """Verify that FeedbackEngine handles empty sessions without crashing."""
    session = PracticeSession(session_id="empty", mode="HR Interview")
    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session)
    evaluation = EvaluationEngine().evaluate(analysis)

    feedback_engine = FeedbackEngine()
    feedback = feedback_engine.generate_feedback(analysis, evaluation, session)

    assert feedback.session_id == "empty"
    assert len(feedback.items) > 0
    # Insufficient evidence notes should be present
    assert len(feedback.insufficient_evidence_notes) > 0


def test_insufficient_evidence_not_penalized_as_failure():
    """Verify that dimensions with insufficient evidence do not generate punitive feedback."""
    dim = ScoreDimension(
        name="Question Handling",
        score=0.0,
        weight=1.0,
        status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
        evidence=["No questions detected."],
        rationale="Insufficient evidence: No questions posed.",
    )
    analysis = ConversationAnalysis(
        session_id="s1",
        mode="HR Interview",
        difficulty="Intermediate",
        scenario_id="sc1",
        persona_id="p1",
        total_turns=0,
        user_message_count=0,
        assistant_message_count=0,
        total_user_words=0,
        total_user_sentences=0,
        avg_words_per_response=0.0,
    )

    item = explain_question_handling(dim, analysis)
    assert item.status == "insufficient_evidence"
    assert item.score is None
    assert "No questions" in item.what
    assert "practice a scenario" in item.action.lower()


def test_not_applicable_dimension_handling():
    """Verify that not_applicable dimensions generate clear, non-punitive explanations."""
    dim = ScoreDimension(
        name="Scenario Alignment & Topic Coverage",
        score=0.0,
        weight=1.0,
        status=DimensionStatus.NOT_APPLICABLE.value,
        evidence=["No expected topics configured."],
        rationale="Not applicable: Open-ended scenario.",
    )
    analysis = ConversationAnalysis(
        session_id="s1",
        mode="Client Pitch",
        difficulty="Intermediate",
        scenario_id="sc1",
        persona_id="p1",
        total_turns=1,
        user_message_count=1,
        assistant_message_count=1,
        total_user_words=25,
        total_user_sentences=2,
        avg_words_per_response=25.0,
    )

    item = explain_topic_coverage(dim, analysis)
    assert item.status == "not_applicable"
    assert item.score is None
    assert item.priority == FeedbackPriority.LOW.value
    assert "No specific required topic checklist" in item.what


def test_heavy_filler_conversation_feedback():
    """Verify objective language-based indicators for conversations with high filler words."""
    session = PracticeSession(session_id="fillers", mode="HR Interview")
    session.add_message(MessageRole.ASSISTANT.value, "What is your greatest strength?")
    session.add_message(
        MessageRole.USER.value,
        "Um, like, basically I guess my greatest strength is, you know, debugging, like, when things break."
    )
    session.turn_number = 1

    analysis = ConversationAnalyzer().analyze(session)
    evaluation = EvaluationEngine().evaluate(analysis)
    feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)

    item_dims = {item.dimension: item for item in feedback.items}
    comm_item = item_dims["Communication & Fluency"]

    assert "filler" in comm_item.what.lower()
    assert "language-based confidence indicator" in comm_item.what.lower()
    assert "silent pause" in comm_item.action.lower()


# ==============================================================================
# 7. Language Safety Tests
# ==============================================================================

def test_language_safety_no_psychological_claims():
    """Verify that feedback across all modes and conditions NEVER outputs forbidden psychological claims."""
    forbidden_phrases = [
        "you are nervous",
        "you lack confidence",
        "you have anxiety",
        "you are introverted",
        "you are not a natural leader",
        "your anxiety",
        "timid personality",
    ]

    modes = [
        "HR Interview",
        "Technical Interview",
        "Client Pitch",
        "Project Viva",
        "Group Discussion",
        "Managerial Interview",
    ]

    for mode in modes:
        session = PracticeSession(session_id=f"safe-{mode}", mode=mode)
        session.add_message(MessageRole.ASSISTANT.value, "Question?")
        session.add_message(MessageRole.USER.value, "Um, maybe I don't know, like, I think so.")
        session.turn_number = 1

        analysis = ConversationAnalyzer().analyze(session)
        evaluation = EvaluationEngine().evaluate(analysis)
        feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)

        serialized_text = str(feedback.to_dict()).lower()
        for phrase in forbidden_phrases:
            assert phrase not in serialized_text, f"Forbidden psychological claim '{phrase}' found in {mode} feedback."


def test_unanswered_questions_feedback():
    """Verify that unaddressed questions generate High Priority feedback with direct answer action."""
    session = PracticeSession(session_id="unanswered", mode="HR Interview")
    session.add_message(MessageRole.ASSISTANT.value, "Can you describe a specific time you failed and what you learned?")
    session.add_message(MessageRole.USER.value, "I enjoy working with teams and learning new technologies.")
    session.turn_number = 1

    analysis = ConversationAnalyzer().analyze(session)
    evaluation = EvaluationEngine().evaluate(analysis)
    feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)

    item_dims = {item.dimension: item for item in feedback.items}
    q_item = item_dims["Question Handling"]
    assert "direct answer" in q_item.action.lower() or "answer the exact question" in q_item.action.lower()
    assert q_item.priority in [FeedbackPriority.HIGH.value, FeedbackPriority.MEDIUM.value]


def test_missing_topics_feedback():
    """Verify that missing expected topics generate specific feedback naming the missing topics."""
    scenario = Scenario(
        id="sc-topics",
        name="Topic Test",
        mode="HR Interview",
        description="Test",
        difficulty="Intermediate",
        persona="Recruiter",
        objective="Test",
        expected_topics=["Conflict Resolution", "Budget Management", "Technical Mentorship"],
        opening_message="Hello",
        max_turns=3,
    )
    session = PracticeSession(session_id="missing-top", mode="HR Interview")
    session.add_message(MessageRole.ASSISTANT.value, "Tell me about your experience.")
    session.add_message(MessageRole.USER.value, "I mentor junior developers on technical architecture.")
    session.turn_number = 1

    analysis = ConversationAnalyzer().analyze(session, scenario=scenario)
    evaluation = EvaluationEngine().evaluate(analysis, scenario=scenario)
    feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session, scenario=scenario)

    item_dims = {item.dimension: item for item in feedback.items}
    topic_item = item_dims["Scenario Alignment & Topic Coverage"]
    assert "not detected" in topic_item.what.lower() or "missing" in topic_item.what.lower()
    assert "actively integrate" in topic_item.action.lower() or "mentally checklist" in topic_item.action.lower()


def test_repeated_phrases_feedback():
    """Verify that repeated phrases are explicitly highlighted in communication feedback."""
    session = PracticeSession(session_id="rep", mode="HR Interview")
    session.add_message(MessageRole.ASSISTANT.value, "What is your approach?")
    session.add_message(
        MessageRole.USER.value,
        "At the end of the day we built the app. At the end of the day we verified it. At the end of the day the customer was happy."
    )
    session.turn_number = 1

    analysis = ConversationAnalyzer().analyze(session)
    evaluation = EvaluationEngine().evaluate(analysis)
    feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)

    item_dims = {item.dimension: item for item in feedback.items}
    comm_item = item_dims["Communication & Fluency"]
    assert "repetitive" in comm_item.what.lower() or "repeated" in comm_item.what.lower() or comm_item.score < 100.0


def test_contradiction_evidence_feedback():
    """Verify that potential contradictions trigger consistency feedback in modes evaluating relevance."""
    session = PracticeSession(session_id="contra", mode="Group Discussion")
    session.add_message(MessageRole.ASSISTANT.value, "Tell me about your team.")
    session.add_message(
        MessageRole.USER.value,
        "I was the solo engineer who built everything alone without any assistance. "
        "Our team of 15 senior developers worked closely together every day on the project."
    )
    session.turn_number = 1

    analysis = ConversationAnalyzer().analyze(session)
    evaluation = EvaluationEngine().evaluate(analysis)
    feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)

    item_dims = {item.dimension: item for item in feedback.items}
    assert "Relevance & Substance" in item_dims
    rel_item = item_dims["Relevance & Substance"]
    if analysis.potential_contradictions:
        assert "contradiction" in rel_item.what.lower()
        assert rel_item.priority == FeedbackPriority.HIGH.value


def test_one_turn_short_answer_edge_case():
    """Verify single-word or minimal input turns handle feedback without errors."""
    session = PracticeSession(session_id="short", mode="Technical Interview")
    session.add_message(MessageRole.ASSISTANT.value, "Have you used Redis?")
    session.add_message(MessageRole.USER.value, "Yes.")
    session.turn_number = 1

    analysis = ConversationAnalyzer().analyze(session)
    evaluation = EvaluationEngine().evaluate(analysis)
    feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)

    assert feedback.session_id == "short"
    assert len(feedback.items) > 0
    assert len(feedback.improvements) > 0


def test_all_modes_action_completeness():
    """Verify that all 6 modes generate non-empty WHAT, WHY, EVIDENCE, IMPACT, ACTION across all dimensions."""
    modes = [
        "HR Interview",
        "Technical Interview",
        "Client Pitch",
        "Project Viva",
        "Group Discussion",
        "Managerial Interview",
    ]

    for mode in modes:
        session = PracticeSession(session_id=f"comp-{mode}", mode=mode)
        session.add_message(MessageRole.ASSISTANT.value, "Let's begin.")
        session.add_message(
            MessageRole.USER.value,
            "In my past role, I implemented a scalable distributed pipeline that improved throughput by 40%."
        )
        session.turn_number = 1

        analysis = ConversationAnalyzer().analyze(session)
        evaluation = EvaluationEngine().evaluate(analysis)
        feedback = FeedbackEngine().generate_feedback(analysis, evaluation, session)

        assert feedback.overall_summary != ""
        for item in feedback.items:
            assert item.what != "", f"Empty what in {mode} -> {item.dimension}"
            assert item.why != "", f"Empty why in {mode} -> {item.dimension}"
            assert item.evidence != "", f"Empty evidence in {mode} -> {item.dimension}"
            assert item.impact != "", f"Empty impact in {mode} -> {item.dimension}"
            assert item.action != "", f"Empty action in {mode} -> {item.dimension}"

