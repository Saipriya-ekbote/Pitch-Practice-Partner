"""
Conversation models for Pitch Practice Partner.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional


def get_current_iso_timestamp() -> str:
    """Generate ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class MessageRole(str, Enum):
    """Supported roles in a conversation turn."""
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"


class SessionStatus(str, Enum):
    """Lifecycle status of a practice session."""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class ConversationMessage:
    """
    Represents an individual message in a practice conversation.
    
    Attributes:
        role: Role of the speaker (system, assistant, user).
        content: Text content of the message.
        timestamp: ISO format timestamp string or datetime representation.
    """
    role: str
    content: str
    timestamp: str = field(default_factory=get_current_iso_timestamp)

    def __post_init__(self) -> None:
        """Validate role and content upon creation."""
        valid_roles = {r.value for r in MessageRole}
        if self.role not in valid_roles:
            raise ValueError(f"Invalid message role '{self.role}'. Allowed: {valid_roles}")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("Message content must be a non-empty string.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """Construct ConversationMessage from a dictionary."""
        return cls(
            role=str(data.get("role", "user")).strip(),
            content=str(data.get("content", "")).strip(),
            timestamp=str(data.get("timestamp", get_current_iso_timestamp())),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ConversationMessage to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }


@dataclass
class PracticeSession:
    """
    Represents an active or completed practice session.
    
    Attributes:
        session_id: Unique UUID string for the session.
        scenario_id: ID of the scenario being practiced.
        persona_id: ID of the AI persona in this session.
        mode: Practice mode (e.g., 'Client Pitch').
        difficulty: Difficulty level (Beginner, Intermediate, Advanced).
        conversation_history: Chronological list of conversation messages.
        turn_number: Count of user-assistant interaction turns completed.
        max_turns: Maximum allowed interaction turns for this session.
        started_at: Timestamp when the session was initialized.
        ended_at: Timestamp when the session completed or was terminated.
        status: Current session lifecycle status (not_started, active, completed).
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str = ""
    persona_id: str = ""
    mode: str = ""
    difficulty: str = "Intermediate"
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    turn_number: int = 0
    max_turns: int = 5
    started_at: str = field(default_factory=get_current_iso_timestamp)
    ended_at: Optional[str] = None
    status: str = SessionStatus.NOT_STARTED.value

    def is_active(self) -> bool:
        """Check if the session is currently active and can receive input."""
        return self.status == SessionStatus.ACTIVE.value and self.turn_number < self.max_turns

    def is_completed(self) -> bool:
        """Check if the session has concluded."""
        return self.status == SessionStatus.COMPLETED.value or self.turn_number >= self.max_turns

    def add_message(self, role: str, content: str) -> ConversationMessage:
        """Helper to create and append a validated message to conversation history."""
        msg = ConversationMessage(role=role, content=content)
        self.conversation_history.append(msg)
        return msg

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PracticeSession":
        """Construct PracticeSession from a dictionary."""
        history = [
            ConversationMessage.from_dict(m) if isinstance(m, dict) else m
            for m in data.get("conversation_history", [])
        ]
        return cls(
            session_id=str(data.get("session_id", str(uuid.uuid4()))),
            scenario_id=str(data.get("scenario_id", "")),
            persona_id=str(data.get("persona_id", "")),
            mode=str(data.get("mode", "")),
            difficulty=str(data.get("difficulty", "Intermediate")),
            conversation_history=history,
            turn_number=int(data.get("turn_number", 0)),
            max_turns=int(data.get("max_turns", 5)),
            started_at=str(data.get("started_at", get_current_iso_timestamp())),
            ended_at=data.get("ended_at"),
            status=str(data.get("status", SessionStatus.NOT_STARTED.value)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert PracticeSession to dictionary."""
        return {
            "session_id": self.session_id,
            "scenario_id": self.scenario_id,
            "persona_id": self.persona_id,
            "mode": self.mode,
            "difficulty": self.difficulty,
            "conversation_history": [m.to_dict() for m in self.conversation_history],
            "turn_number": self.turn_number,
            "max_turns": self.max_turns,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": self.status,
        }
