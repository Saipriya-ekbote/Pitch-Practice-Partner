"""
Data models for Conversation Intelligence and Evidence Extraction.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ResponseFeature:
    """
    Deterministic linguistic measurements for a single candidate response turn.
    
    Attributes:
        turn_number: Sequential turn index (1-indexed).
        text: Raw text of the user response.
        word_count: Total word count in this response.
        sentence_count: Estimated sentence count based on punctuation.
        avg_sentence_length: Average words per sentence.
        length_category: Classification (short < 20 words, medium 20-60, long > 60).
    """
    turn_number: int
    text: str
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    length_category: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert ResponseFeature to dictionary."""
        return {
            "turn_number": self.turn_number,
            "text": self.text,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "avg_sentence_length": round(self.avg_sentence_length, 2),
            "length_category": self.length_category,
        }


@dataclass
class QuestionEvidence:
    """
    Evidence of a question posed by the AI and how the candidate addressed it.
    
    Attributes:
        turn_number: Turn when the AI asked the question.
        question_text: The extracted question string.
        detected_topic: Inferred primary topic of the question.
        status: Heuristic assessment ('addressed', 'partially_addressed', 'unaddressed').
        user_response_turn: Turn of user's answer (if applicable).
    """
    turn_number: int
    question_text: str
    detected_topic: str = ""
    status: str = "addressed"
    user_response_turn: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert QuestionEvidence to dictionary."""
        return {
            "turn_number": self.turn_number,
            "question_text": self.question_text,
            "detected_topic": self.detected_topic,
            "status": self.status,
            "user_response_turn": self.user_response_turn,
        }


@dataclass
class ConcernEvidence:
    """
    Evidence regarding a persona concern or objection during the session.
    
    Attributes:
        concern_name: Name of the concern (e.g., 'Security', 'Cost & ROI').
        status: State of the concern ('raised_and_addressed', 'raised_unaddressed', 'not_raised').
        turn_raised: Turn number when AI voiced this concern.
        turn_addressed: Turn number when candidate addressed it.
    """
    concern_name: str
    status: str
    turn_raised: Optional[int] = None
    turn_addressed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert ConcernEvidence to dictionary."""
        return {
            "concern_name": self.concern_name,
            "status": self.status,
            "turn_raised": self.turn_raised,
            "turn_addressed": self.turn_addressed,
        }


@dataclass
class ObjectionEvidence:
    """
    Evidence regarding a specific objection raised by the AI persona.
    
    Attributes:
        objection_text: The pushback statement or objection raised.
        objection_type: Category of objection (e.g., 'High Cost', 'Compliance Risk').
        turn_raised: Turn when AI raised the objection.
        addressed: Whether candidate provided mitigating evidence or explanation.
    """
    objection_text: str
    objection_type: str
    turn_raised: int
    addressed: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert ObjectionEvidence to dictionary."""
        return {
            "objection_text": self.objection_text,
            "objection_type": self.objection_type,
            "turn_raised": self.turn_raised,
            "addressed": self.addressed,
        }


@dataclass
class ModeSpecificEvidence:
    """
    Domain-specific conversational indicators tailored to the selected practice mode.
    
    Attributes:
        mode: The practice mode name.
        indicators: Dictionary of detected domain components and observable signals.
    """
    mode: str
    indicators: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ModeSpecificEvidence to dictionary."""
        return {
            "mode": self.mode,
            "indicators": self.indicators,
        }


@dataclass
class ConversationAnalysis:
    """
    Complete structured conversation intelligence report for a practice session.
    Represents pure evidence and observations without performance scoring or grading.
    """
    session_id: str
    mode: str
    difficulty: str
    scenario_id: str
    persona_id: str
    total_turns: int
    user_message_count: int
    assistant_message_count: int
    total_user_words: int
    total_user_sentences: int
    avg_words_per_response: float
    
    # Response linguistic features
    response_features: List[ResponseFeature] = field(default_factory=list)
    
    # Filler word metrics
    filler_word_counts: Dict[str, int] = field(default_factory=dict)
    total_filler_count: int = 0
    filler_percentage: float = 0.0
    
    # Repetition signals
    repeated_phrases: List[Dict[str, Any]] = field(default_factory=list)
    repeated_words: List[Dict[str, Any]] = field(default_factory=list)
    
    # Question & Answer evidence
    questions_detected: List[QuestionEvidence] = field(default_factory=list)
    answered_questions_count: int = 0
    unanswered_questions_count: int = 0
    
    # Topical Coverage evidence
    topics_discussed: List[str] = field(default_factory=list)
    covered_expected_topics: List[str] = field(default_factory=list)
    missing_expected_topics: List[str] = field(default_factory=list)
    
    # Persona Concerns & Objections
    concerns_evidence: List[ConcernEvidence] = field(default_factory=list)
    objections_evidence: List[ObjectionEvidence] = field(default_factory=list)
    
    # Observations
    missing_information_observations: List[str] = field(default_factory=list)
    potential_contradictions: List[str] = field(default_factory=list)
    
    # Mode-specific analysis
    mode_specific_analysis: Optional[ModeSpecificEvidence] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert complete analysis object to structured dictionary."""
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "difficulty": self.difficulty,
            "scenario_id": self.scenario_id,
            "persona_id": self.persona_id,
            "total_turns": self.total_turns,
            "user_message_count": self.user_message_count,
            "assistant_message_count": self.assistant_message_count,
            "total_user_words": self.total_user_words,
            "total_user_sentences": self.total_user_sentences,
            "avg_words_per_response": round(self.avg_words_per_response, 2),
            "response_features": [rf.to_dict() for rf in self.response_features],
            "filler_word_counts": self.filler_word_counts,
            "total_filler_count": self.total_filler_count,
            "filler_percentage": round(self.filler_percentage, 2),
            "repeated_phrases": self.repeated_phrases,
            "repeated_words": self.repeated_words,
            "questions_detected": [q.to_dict() for q in self.questions_detected],
            "answered_questions_count": self.answered_questions_count,
            "unanswered_questions_count": self.unanswered_questions_count,
            "topics_discussed": self.topics_discussed,
            "covered_expected_topics": self.covered_expected_topics,
            "missing_expected_topics": self.missing_expected_topics,
            "concerns_evidence": [c.to_dict() for c in self.concerns_evidence],
            "objections_evidence": [o.to_dict() for o in self.objections_evidence],
            "missing_information_observations": self.missing_information_observations,
            "potential_contradictions": self.potential_contradictions,
            "mode_specific_analysis": self.mode_specific_analysis.to_dict()
            if self.mode_specific_analysis
            else None,
        }
