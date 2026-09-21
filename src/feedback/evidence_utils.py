"""
Evidence utility functions for Pitch Practice Partner.
Extracts, formats, and safely bounds real conversation evidence without fabrication.
"""

import re
from typing import Optional, List, Tuple
from src.conversation.conversation_models import PracticeSession, MessageRole
from src.intelligence.analysis_models import ConversationAnalysis


def truncate_text(text: str, max_chars: int = 150) -> str:
    """
    Safely truncate text to a maximum character length, avoiding cutting mid-word when possible.
    """
    cleaned = " ".join(text.strip().split())
    if len(cleaned) <= max_chars:
        return cleaned
    
    truncated = cleaned[:max_chars].rsplit(" ", 1)[0]
    if not truncated:
        truncated = cleaned[:max_chars]
    return f"{truncated}..."


def extract_user_turn_snippet(
    session: Optional[PracticeSession],
    turn_num: int,
    max_chars: int = 150
) -> Optional[Tuple[str, str]]:
    """
    Extract exact user transcript text for a specific turn number (1-indexed).
    
    Returns:
        Tuple of (snippet_text, source_ref) or None if turn not found.
    """
    if not session or not session.conversation_history:
        return None

    user_turn = 0
    for msg in session.conversation_history:
        if msg.role == MessageRole.USER.value:
            user_turn += 1
            if user_turn == turn_num:
                snippet = truncate_text(msg.content, max_chars)
                return (snippet, f"Turn {turn_num}")
    return None


def find_matching_user_snippet(
    session: Optional[PracticeSession],
    keywords: List[str],
    max_chars: int = 150
) -> Optional[Tuple[str, str]]:
    """
    Search user messages for given keywords and return the first matching excerpt.
    
    Returns:
        Tuple of (snippet_text, source_ref) or None if no match found.
    """
    if not session or not session.conversation_history or not keywords:
        return None

    user_turn = 0
    for msg in session.conversation_history:
        if msg.role == MessageRole.USER.value:
            user_turn += 1
            content_lower = msg.content.lower()
            for kw in keywords:
                if kw.lower() in content_lower:
                    snippet = truncate_text(msg.content, max_chars)
                    return (snippet, f"Turn {user_turn}")
    return None


def extract_first_user_snippet(
    session: Optional[PracticeSession],
    max_chars: int = 150
) -> Optional[Tuple[str, str]]:
    """
    Extract the first user response snippet from the session.
    """
    return extract_user_turn_snippet(session, turn_num=1, max_chars=max_chars)


def format_evidence_display(
    evidence_text: str,
    evidence_type: str = "Analysis observation",
    source_reference: str = ""
) -> str:
    """
    Format evidence with clear, transparent attribution so users know its origin.

    - If the displayed evidence is the user's exact transcript words:
      [Transcript excerpt — Turn X]: "exact transcript text"
    - If it is a derived metric/observation (e.g. "Time complexity analysis: Detected..."):
      [Analysis observation]: observation text
    - Derived analysis observations are never presented as transcript excerpts.
    """
    # Guard against presenting derived observations/metrics as transcript excerpts
    derived_signals = ["analysis:", "detected", "unaddressed", "filler words", "scored ≥", "dimensions scored"]
    is_derived = any(sig in evidence_text.lower() for sig in derived_signals)

    if is_derived or evidence_type != "Transcript excerpt":
        return f"[Analysis observation]: {evidence_text}"

    prefix = f"{evidence_type} — {source_reference}" if source_reference else evidence_type
    stripped = evidence_text.strip()
    if (stripped.startswith('"') and stripped.endswith('"')) or (stripped.startswith("'") and stripped.endswith("'")):
        return f"[{prefix}]: {stripped}"
    return f"[{prefix}]: \"{evidence_text}\""
