"""
Scenario and Persona data models for Pitch Practice Partner.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# Standard practice modes supported across the application
PRACTICE_MODES = [
    "HR Interview",
    "Technical Interview",
    "Client Pitch",
    "Project Viva",
    "Group Discussion",
    "Managerial Interview",
]

# Standard difficulty tiers
DIFFICULTY_LEVELS = [
    "Beginner",
    "Intermediate",
    "Advanced",
]


@dataclass
class Persona:
    """
    Represents an AI conversational persona.
    
    Attributes:
        id: Unique identifier for the persona (e.g. 'persona_hr_friendly').
        name: Short descriptive name of the persona (e.g. 'Friendly HR Recruiter').
        role: Professional title or role (e.g. 'Senior Talent Acquisition Specialist').
        personality: Core personality traits (e.g. 'Approachable, encouraging').
        background: Contextual professional background.
        objective: Primary conversational goal for this persona.
        knowledge_level: Domain expertise level.
        communication_style: Tone, pacing, and vocabulary.
        concerns: Specific topics or vulnerabilities the persona probes.
        behaviors: Observational behavioral traits and follow-up habits.
        objection_types: Categories of pushback or critical inquiries raised.
        follow_up_strategy: How the persona probes vague or incomplete responses.
        difficulty: Calibrated difficulty tier (Beginner, Intermediate, Advanced).
        supported_modes: List of practice modes this persona is suitable for.
    """
    id: str
    name: str
    role: str
    personality: str
    background: str
    objective: str
    knowledge_level: str
    communication_style: str
    concerns: List[str] = field(default_factory=list)
    behaviors: List[str] = field(default_factory=list)
    objection_types: List[str] = field(default_factory=list)
    follow_up_strategy: str = ""
    difficulty: str = "Intermediate"
    supported_modes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate essential fields upon instantiation."""
        if not self.id or not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Persona 'id' must be a non-empty string.")
        if not self.name or not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Persona 'name' must be a non-empty string.")
        if not self.role or not isinstance(self.role, str) or not self.role.strip():
            raise ValueError("Persona 'role' must be a non-empty string.")
        if self.difficulty not in DIFFICULTY_LEVELS:
            raise ValueError(
                f"Invalid persona difficulty '{self.difficulty}'. Allowed difficulties: {DIFFICULTY_LEVELS}"
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Persona":
        """Construct a Persona instance from a dictionary."""
        return cls(
            id=str(data.get("id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            role=str(data.get("role", "")).strip(),
            personality=str(data.get("personality", "")),
            background=str(data.get("background", "")),
            objective=str(data.get("objective", "")),
            knowledge_level=str(data.get("knowledge_level", "")),
            communication_style=str(data.get("communication_style", "")),
            concerns=list(data.get("concerns", [])),
            behaviors=list(data.get("behaviors", [])),
            objection_types=list(data.get("objection_types", [])),
            follow_up_strategy=str(data.get("follow_up_strategy", "")),
            difficulty=str(data.get("difficulty", "Intermediate")),
            supported_modes=list(data.get("supported_modes", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Persona instance to a dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "personality": self.personality,
            "background": self.background,
            "objective": self.objective,
            "knowledge_level": self.knowledge_level,
            "communication_style": self.communication_style,
            "concerns": self.concerns,
            "behaviors": self.behaviors,
            "objection_types": self.objection_types,
            "follow_up_strategy": self.follow_up_strategy,
            "difficulty": self.difficulty,
            "supported_modes": self.supported_modes,
        }


@dataclass
class Scenario:
    """
    Represents an interactive practice scenario.
    
    Attributes:
        id: Unique identifier for the scenario (e.g. 'hr_intro_01').
        name: Short descriptive title of the scenario.
        mode: The category/mode of practice (must be in PRACTICE_MODES).
        description: A concise overview of what the candidate practices.
        difficulty: The target difficulty level (Beginner, Intermediate, Advanced).
        persona_id: Reference identifier to the associated Persona.
        persona: Textual description/name of the persona (for backwards compatibility).
        objective: Primary goal of the scenario (for backwards compatibility).
        conversation_goal: Specific goal for candidate to accomplish.
        expected_topics: List of key topics or competencies evaluated.
        forbidden_topics: Topics or pitfalls the candidate should avoid.
        opening_message: Initial prompt/greeting by the AI.
        max_turns: Maximum conversation turns planned.
        maximum_turns: Alias for max_turns.
    """
    id: str
    name: str
    mode: str
    description: str
    difficulty: str
    persona_id: str = ""
    persona: str = ""
    objective: str = ""
    conversation_goal: str = ""
    expected_topics: List[str] = field(default_factory=list)
    forbidden_topics: List[str] = field(default_factory=list)
    opening_message: str = ""
    max_turns: int = 5

    def __post_init__(self) -> None:
        """Validate essential fields upon instantiation."""
        if not self.id or not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Scenario 'id' must be a non-empty string.")
        if not self.name or not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Scenario 'name' must be a non-empty string.")
        if self.mode not in PRACTICE_MODES:
            raise ValueError(
                f"Invalid scenario mode '{self.mode}'. Allowed modes: {PRACTICE_MODES}"
            )
        if self.difficulty not in DIFFICULTY_LEVELS:
            raise ValueError(
                f"Invalid scenario difficulty '{self.difficulty}'. Allowed difficulties: {DIFFICULTY_LEVELS}"
            )
        # Ensure conversation_goal and objective are synchronized
        if not self.conversation_goal and self.objective:
            self.conversation_goal = self.objective
        elif not self.objective and self.conversation_goal:
            self.objective = self.conversation_goal

    @property
    def maximum_turns(self) -> int:
        """Alias for max_turns."""
        return self.max_turns

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        """Construct a Scenario instance from a dictionary."""
        goal = str(data.get("conversation_goal", data.get("objective", "")))
        turns = int(data.get("maximum_turns", data.get("max_turns", 5)))
        return cls(
            id=str(data.get("id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            mode=str(data.get("mode", "")).strip(),
            description=str(data.get("description", "")),
            difficulty=str(data.get("difficulty", "")),
            persona_id=str(data.get("persona_id", "")),
            persona=str(data.get("persona", "")),
            objective=goal,
            conversation_goal=goal,
            expected_topics=list(data.get("expected_topics", [])),
            forbidden_topics=list(data.get("forbidden_topics", [])),
            opening_message=str(data.get("opening_message", "")),
            max_turns=turns,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Scenario instance to a dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "description": self.description,
            "difficulty": self.difficulty,
            "persona_id": self.persona_id,
            "persona": self.persona,
            "objective": self.objective,
            "conversation_goal": self.conversation_goal,
            "expected_topics": self.expected_topics,
            "forbidden_topics": self.forbidden_topics,
            "opening_message": self.opening_message,
            "max_turns": self.max_turns,
            "maximum_turns": self.max_turns,
        }
