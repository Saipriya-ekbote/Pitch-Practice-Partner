"""
Conversation Analyzer orchestrating deterministic and heuristic conversation intelligence extraction.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from src.conversation.conversation_models import PracticeSession, MessageRole
from src.scenarios.scenario_models import Scenario, Persona
from src.intelligence.analysis_models import (
    ConversationAnalysis,
    ResponseFeature,
    QuestionEvidence,
    ConcernEvidence,
    ObjectionEvidence,
    ModeSpecificEvidence,
)
from src.intelligence.detectors import (
    extract_response_features,
    detect_filler_words,
    detect_repetitions,
    extract_questions_from_text,
    assess_question_alignment,
    detect_potential_contradictions,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# Mode-Specific Analysis Strategy Pattern
# ==============================================================================

class ModeAnalysisStrategy(ABC):
    """Abstract Strategy interface for extracting mode-specific conversational indicators."""

    @abstractmethod
    def analyze(self, user_texts: List[str], assistant_texts: List[str]) -> ModeSpecificEvidence:
        pass


class HRInterviewStrategy(ModeAnalysisStrategy):
    """Analyzes behavioral HR interviews for STAR framework components."""

    def analyze(self, user_texts: List[str], assistant_texts: List[str]) -> ModeSpecificEvidence:
        combined_user = " ".join(user_texts).lower()

        star_patterns = {
            "Situation": [
                r"\b(situation|context|at my previous|when i was at|back when|in my last role)\b",
                r"\b(project where|team was facing)\b",
            ],
            "Task": [
                r"\b(task|goal|objective|assigned to|needed to|responsible for|target was)\b",
            ],
            "Action": [
                r"\b(i decided|i implemented|i designed|i built|i led|i took the initiative)\b",
                r"\b(my approach|i organized|i scheduled|i analyzed)\b",
            ],
            "Result": [
                r"\b(result|outcome|increased by|decreased by|reduced|saved|improved|delivered)\b",
                r"\b(\d+%\s*increase|\d+%\s*reduction|successful launch)\b",
            ],
        }

        indicators: Dict[str, Any] = {"star_components": {}}
        for comp, patterns in star_patterns.items():
            detected = any(re.search(pat, combined_user) for pat in patterns)
            indicators["star_components"][comp] = "detected" if detected else "not_detected"

        # Check for concrete examples versus generalities
        has_specific_metric = bool(re.search(r"\b\d+(\.\d+)?%|\$\d+|\b\d+\s*(days|weeks|months|engineers|users)\b", combined_user))
        indicators["specific_metrics_provided"] = "detected" if has_specific_metric else "not_detected"

        return ModeSpecificEvidence(mode="HR Interview", indicators=indicators)


class TechnicalInterviewStrategy(ModeAnalysisStrategy):
    """Analyzes technical interviews for complexity concepts and architecture signals."""

    def analyze(self, user_texts: List[str], assistant_texts: List[str]) -> ModeSpecificEvidence:
        combined_user = " ".join(user_texts).lower()

        concepts = {
            "Time Complexity": bool(re.search(r"\b(o\([^)]+\)|time complexity|linear time|logarithmic|constant time|quadratic)\b", combined_user)),
            "Space / Memory Overhead": bool(re.search(r"\b(space complexity|memory footprint|auxiliary space|ram|in-memory)\b", combined_user)),
            "Data Structures": bool(re.search(r"\b(heap|hash map|hashmap|tree|array|queue|stack|graph|trie|cache|redis)\b", combined_user)),
            "Edge Cases & Boundary Conditions": bool(re.search(r"\b(edge case|null|empty|overflow|boundary|negative|duplicate|concurrency)\b", combined_user)),
            "System Architecture & Scaling": bool(re.search(r"\b(distributed|throughput|latency|sharding|partition|replication|fault tolerance)\b", combined_user)),
        }

        indicators: Dict[str, Any] = {
            "technical_concepts": {k: ("detected" if v else "not_detected") for k, v in concepts.items()}
        }
        return ModeSpecificEvidence(mode="Technical Interview", indicators=indicators)


class ClientPitchStrategy(ModeAnalysisStrategy):
    """Analyzes client and executive pitches for business metrics, ROI, and objection handling."""

    def analyze(self, user_texts: List[str], assistant_texts: List[str]) -> ModeSpecificEvidence:
        combined_user = " ".join(user_texts).lower()

        pitch_signals = {
            "Value Proposition": bool(re.search(r"\b(value proposition|competitive advantage|solution|transform|streamline|accelerate)\b", combined_user)),
            "Cost & ROI Justification": bool(re.search(r"\b(roi|return on investment|payback|cost reduction|save|budget|pricing model)\b", combined_user)),
            "Security & Compliance": bool(re.search(r"\b(security|gdpr|soc-?2|hipaa|encryption|compliance|data privacy|audit)\b", combined_user)),
            "Scalability & Performance": bool(re.search(r"\b(scale|scaling|uptime|sla|latency|throughput|integration)\b", combined_user)),
            "Concrete Evidence / Case Studies": bool(re.search(r"\b(\d+%\s*reduction|\d+x\s*faster|case study|benchmark|proven)\b", combined_user)),
        }

        indicators: Dict[str, Any] = {
            "pitch_components": {k: ("detected" if v else "not_detected") for k, v in pitch_signals.items()}
        }
        return ModeSpecificEvidence(mode="Client Pitch", indicators=indicators)


class ProjectVivaStrategy(ModeAnalysisStrategy):
    """Analyzes project defenses for methodology rigor, stack rationale, and limitations."""

    def analyze(self, user_texts: List[str], assistant_texts: List[str]) -> ModeSpecificEvidence:
        combined_user = " ".join(user_texts).lower()

        viva_signals = {
            "Architecture & Design Justification": bool(re.search(r"\b(architecture|design pattern|modular|mvc|microservices|pipeline)\b", combined_user)),
            "Technology Stack Rationale": bool(re.search(r"\b(chose|selected|evaluated|compared to|trade-off|over alternatives)\b", combined_user)),
            "Methodology & Experimental Rigor": bool(re.search(r"\b(methodology|algorithm|dataset|validation|split|f1|accuracy|baseline)\b", combined_user)),
            "Awareness of Limitations": bool(re.search(r"\b(limitation|future work|bottleneck|constraint|room for improvement)\b", combined_user)),
        }

        indicators: Dict[str, Any] = {
            "viva_components": {k: ("detected" if v else "not_detected") for k, v in viva_signals.items()}
        }
        return ModeSpecificEvidence(mode="Project Viva", indicators=indicators)


class GroupDiscussionStrategy(ModeAnalysisStrategy):
    """Analyzes collaborative group discussions for synthesis, viewpoints, and active debate."""

    def analyze(self, user_texts: List[str], assistant_texts: List[str]) -> ModeSpecificEvidence:
        combined_user = " ".join(user_texts).lower()

        gd_signals = {
            "Constructive Agreement / Building On Ideas": bool(re.search(r"\b(i agree|building on|valid point|to add to that|complementing)\b", combined_user)),
            "Respectful Counter-Argument / Nuance": bool(re.search(r"\b(however|on the other hand|alternatively|another perspective|counter-argument)\b", combined_user)),
            "Synthesis / Common Ground": bool(re.search(r"\b(in summary|to summarize|balance between|consensus|moving forward)\b", combined_user)),
            "Evidence-Backed Reasoning": bool(re.search(r"\b(studies show|data suggests|for instance|for example|statistically)\b", combined_user)),
        }

        indicators: Dict[str, Any] = {
            "discussion_dynamics": {k: ("detected" if v else "not_detected") for k, v in gd_signals.items()}
        }
        return ModeSpecificEvidence(mode="Group Discussion", indicators=indicators)


class ManagerialInterviewStrategy(ModeAnalysisStrategy):
    """Analyzes managerial leadership scenarios for conflict mediation, ownership, and prioritization."""

    def analyze(self, user_texts: List[str], assistant_texts: List[str]) -> ModeSpecificEvidence:
        combined_user = " ".join(user_texts).lower()

        managerial_signals = {
            "Empathetic Leadership & 1-on-1 Communication": bool(re.search(r"\b(1-on-1|one on one|listen|empathy|psychological safety|coaching)\b", combined_user)),
            "Conflict Mediation & De-escalation": bool(re.search(r"\b(conflict|disagreement|alignment|common ground|mediate|facilitate)\b", combined_user)),
            "Prioritization Frameworks": bool(re.search(r"\b(rice|prioritize|urgent vs important|trade-off|roadmap|triage)\b", combined_user)),
            "Ownership & Accountability": bool(re.search(r"\b(ownership|accountability|responsible|retrospective|lesson learned)\b", combined_user)),
            "Stakeholder Transparency": bool(re.search(r"\b(stakeholder|executive|transparent|expectations|alignment|saying no)\b", combined_user)),
        }

        indicators: Dict[str, Any] = {
            "leadership_signals": {k: ("detected" if v else "not_detected") for k, v in managerial_signals.items()}
        }
        return ModeSpecificEvidence(mode="Managerial Interview", indicators=indicators)


STRATEGY_REGISTRY: Dict[str, ModeAnalysisStrategy] = {
    "HR Interview": HRInterviewStrategy(),
    "Technical Interview": TechnicalInterviewStrategy(),
    "Client Pitch": ClientPitchStrategy(),
    "Project Viva": ProjectVivaStrategy(),
    "Group Discussion": GroupDiscussionStrategy(),
    "Managerial Interview": ManagerialInterviewStrategy(),
}


# ==============================================================================
# Central Conversation Analyzer
# ==============================================================================

class ConversationAnalyzer:
    """
    Central analyzer that extracts structured linguistic and domain evidence from a completed session.
    Operates strictly in read-only mode without scoring or evaluating performance.
    """

    def analyze(
        self,
        session: PracticeSession,
        scenario: Optional[Scenario] = None,
        persona: Optional[Persona] = None,
    ) -> ConversationAnalysis:
        """
        Extract complete conversation intelligence evidence for a given practice session.
        
        Args:
            session: The PracticeSession transcript.
            scenario: Optional Scenario metadata.
            persona: Optional Persona metadata.
            
        Returns:
            A populated, structured ConversationAnalysis instance.
        """
        # Separate user and assistant messages in chronological order
        user_messages = [m for m in session.conversation_history if m.role == MessageRole.USER.value]
        assistant_messages = [m for m in session.conversation_history if m.role == MessageRole.ASSISTANT.value]

        user_texts = [m.content for m in user_messages]
        assistant_texts = [m.content for m in assistant_messages]

        # 1. Response Linguistic Features (Deterministic)
        response_features: List[ResponseFeature] = []
        total_user_words = 0
        total_user_sentences = 0
        all_filler_counts: Dict[str, int] = {}

        for idx, text in enumerate(user_texts, start=1):
            rf = extract_response_features(turn_number=idx, text=text)
            response_features.append(rf)
            total_user_words += rf.word_count
            total_user_sentences += rf.sentence_count

            turn_fillers = detect_filler_words(text)
            for f_word, count in turn_fillers.items():
                all_filler_counts[f_word] = all_filler_counts.get(f_word, 0) + count

        total_filler_count = sum(all_filler_counts.values())
        filler_percentage = (
            (total_filler_count / total_user_words * 100) if total_user_words > 0 else 0.0
        )
        avg_words = (
            (total_user_words / len(user_texts)) if user_texts else 0.0
        )

        # 2. Repetition Analysis (Deterministic)
        repeated_phrases, repeated_words = detect_repetitions(user_texts)

        # 3. Question Detection & Alignment Analysis (Heuristic)
        questions_detected: List[QuestionEvidence] = []
        q_idx = 1
        for a_idx, a_msg in enumerate(assistant_messages):
            extracted_qs = extract_questions_from_text(a_msg.content)
            for q_str in extracted_qs:
                # Find matching user response (if any)
                user_ans = user_texts[a_idx] if a_idx < len(user_texts) else ""
                status = assess_question_alignment(q_str, user_ans)
                user_turn = (a_idx + 1) if a_idx < len(user_texts) else None

                questions_detected.append(
                    QuestionEvidence(
                        turn_number=q_idx,
                        question_text=q_str,
                        detected_topic=self._infer_topic_from_text(q_str),
                        status=status,
                        user_response_turn=user_turn,
                    )
                )
                q_idx += 1

        answered_count = sum(1 for q in questions_detected if q.status == "addressed")
        unanswered_count = sum(1 for q in questions_detected if q.status == "unaddressed")

        # 4. Topical Coverage Evidence
        topics_discussed = self._extract_discussed_topics(user_texts, scenario)
        expected_topics = scenario.expected_topics if scenario else []
        covered_expected: List[str] = []
        missing_expected: List[str] = []

        combined_user_lower = " ".join(user_texts).lower()
        for exp_topic in expected_topics:
            topic_tokens = re.findall(r"\b[a-z]{3,}\b", exp_topic.lower())
            if any(tok in combined_user_lower for tok in topic_tokens):
                covered_expected.append(exp_topic)
            else:
                missing_expected.append(exp_topic)

        # 5. Persona Concerns & Objections Evidence
        concerns_evidence = self._analyze_persona_concerns(persona, assistant_texts, user_texts)
        objections_evidence = self._analyze_objections(persona, assistant_texts, user_texts)

        # 6. Observations & Contradictions
        missing_info_obs: List[str] = []
        for q in questions_detected:
            if q.status == "unaddressed":
                missing_info_obs.append(
                    f"Question at Turn {q.turn_number} ('{q.question_text[:60]}...') appears unaddressed in candidate response."
                )

        potential_contradictions = detect_potential_contradictions(user_texts)

        # 7. Mode-Specific Evidence Strategy
        mode_strategy = STRATEGY_REGISTRY.get(session.mode)
        mode_analysis = mode_strategy.analyze(user_texts, assistant_texts) if mode_strategy else None

        return ConversationAnalysis(
            session_id=session.session_id,
            mode=session.mode,
            difficulty=session.difficulty,
            scenario_id=session.scenario_id,
            persona_id=session.persona_id,
            total_turns=session.turn_number,
            user_message_count=len(user_messages),
            assistant_message_count=len(assistant_messages),
            total_user_words=total_user_words,
            total_user_sentences=total_user_sentences,
            avg_words_per_response=avg_words,
            response_features=response_features,
            filler_word_counts=all_filler_counts,
            total_filler_count=total_filler_count,
            filler_percentage=filler_percentage,
            repeated_phrases=repeated_phrases,
            repeated_words=repeated_words,
            questions_detected=questions_detected,
            answered_questions_count=answered_count,
            unanswered_questions_count=unanswered_count,
            topics_discussed=topics_discussed,
            covered_expected_topics=covered_expected,
            missing_expected_topics=missing_expected,
            concerns_evidence=concerns_evidence,
            objections_evidence=objections_evidence,
            missing_information_observations=missing_info_obs,
            potential_contradictions=potential_contradictions,
            mode_specific_analysis=mode_analysis,
        )

    def _infer_topic_from_text(self, text: str) -> str:
        """Heuristically assign a category topic to an AI question."""
        lower = text.lower()
        if any(w in lower for w in ["cost", "budget", "price", "roi", "financial"]):
            return "Cost & ROI"
        if any(w in lower for w in ["security", "privacy", "compliance", "gdpr", "safe"]):
            return "Security & Compliance"
        if any(w in lower for w in ["scale", "latency", "architecture", "distributed", "traffic"]):
            return "Architecture & Scalability"
        if any(w in lower for w in ["team", "conflict", "disagreement", "manage", "lead"]):
            return "Leadership & Teamwork"
        if any(w in lower for w in ["why", "rationale", "chose", "alternative", "stack"]):
            return "Design Rationale"
        return "General Inquiry"

    def _extract_discussed_topics(self, user_texts: List[str], scenario: Optional[Scenario]) -> List[str]:
        """Extract meaningful topic domains identified in candidate responses."""
        combined = " ".join(user_texts).lower()
        candidates = [
            ("Security & Privacy", ["security", "privacy", "gdpr", "encryption", "auth"]),
            ("Cost & Return on Investment", ["cost", "budget", "roi", "savings", "financial", "licensing"]),
            ("System Architecture", ["architecture", "microservices", "modular", "database", "cache", "redis"]),
            ("Algorithmic Efficiency", ["algorithm", "complexity", "time complexity", "heap", "scale"]),
            ("Leadership & Culture", ["leadership", "team", "conflict", "culture", "mentoring"]),
            ("Experimental Validation", ["methodology", "dataset", "baseline", "f1", "validation"]),
        ]
        found: List[str] = []
        for topic_name, keywords in candidates:
            if any(k in combined for k in keywords):
                found.append(topic_name)
        return found

    def _analyze_persona_concerns(
        self, persona: Optional[Persona], assistant_texts: List[str], user_texts: List[str]
    ) -> List[ConcernEvidence]:
        """Determine whether persona concerns were raised and addressed."""
        if not persona or not persona.concerns:
            return []

        combined_ai = " ".join(assistant_texts).lower()
        combined_user = " ".join(user_texts).lower()
        evidence_list: List[ConcernEvidence] = []

        for concern in persona.concerns:
            tokens = re.findall(r"\b[a-z]{3,}\b", concern.lower())
            ai_raised = any(tok in combined_ai for tok in tokens)
            user_addressed = any(tok in combined_user for tok in tokens)

            if ai_raised and user_addressed:
                status = "raised_and_addressed"
            elif ai_raised and not user_addressed:
                status = "raised_unaddressed"
            elif not ai_raised and user_addressed:
                status = "proactively_addressed"
            else:
                status = "not_raised"

            evidence_list.append(ConcernEvidence(concern_name=concern, status=status))

        return evidence_list

    def _analyze_objections(
        self, persona: Optional[Persona], assistant_texts: List[str], user_texts: List[str]
    ) -> List[ObjectionEvidence]:
        """Identify potential objections voiced by AI persona and assess if candidate addressed them."""
        if not persona or not persona.objection_types:
            return []

        combined_ai = " ".join(assistant_texts).lower()
        combined_user = " ".join(user_texts).lower()
        objections: List[ObjectionEvidence] = []

        for obj_type in persona.objection_types:
            tokens = re.findall(r"\b[a-z]{3,}\b", obj_type.lower())
            if any(tok in combined_ai for tok in tokens):
                addressed = any(tok in combined_user for tok in tokens)
                objections.append(
                    ObjectionEvidence(
                        objection_text=f"Persona voiced inquiry regarding {obj_type.lower()}",
                        objection_type=obj_type,
                        turn_raised=1,
                        addressed=addressed,
                    )
                )

        return objections
