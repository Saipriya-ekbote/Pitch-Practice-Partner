"""
Deterministic and heuristic linguistic detectors for Conversation Intelligence.
"""

import re
from typing import List, Dict, Any, Tuple, Set

from src.intelligence.analysis_models import ResponseFeature

# Standard English stop words for repetition filtering
STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "did", "do", "does", "doing", "don",
    "down", "during", "each", "few", "for", "from", "further", "had", "has",
    "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off",
    "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out",
    "over", "own", "s", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "will", "with", "would", "you", "your", "yours",
    "yourself", "yourselves",
}


# ==============================================================================
# 1. Response Feature Extraction (Deterministic)
# ==============================================================================

def extract_response_features(turn_number: int, text: str) -> ResponseFeature:
    """
    Compute deterministic linguistic features for a single candidate turn.
    
    Categorization Thresholds:
      - short: < 20 words
      - medium: 20 to 60 words
      - long: > 60 words
    """
    cleaned = text.strip() if text else ""
    words = re.findall(r"\b[\w'-]+\b", cleaned)
    word_count = len(words)

    # Estimate sentence count based on terminal punctuation
    sentences = [s.strip() for s in re.split(r"[.!?]+", cleaned) if s.strip()]
    sentence_count = max(1, len(sentences)) if word_count > 0 else 0

    avg_sentence_length = (word_count / sentence_count) if sentence_count > 0 else 0.0

    if word_count < 20:
        length_category = "short"
    elif word_count <= 60:
        length_category = "medium"
    else:
        length_category = "long"

    return ResponseFeature(
        turn_number=turn_number,
        text=cleaned,
        word_count=word_count,
        sentence_count=sentence_count,
        avg_sentence_length=avg_sentence_length,
        length_category=length_category,
    )


# ==============================================================================
# 2. Filler Word Detection (Context-Aware)
# ==============================================================================

def detect_filler_words(text: str) -> Dict[str, int]:
    """
    Detect filler words and vocalized hesitations with boundary awareness to prevent false positives.
    
    Rules:
      - Unconditional fillers: 'um', 'uh', 'er', 'erm', 'ah'
      - Multi-word fillers: 'you know', 'i mean'
      - Contextual fillers: 'like', 'actually', 'basically', 'so'
        - 'like': only counted when isolated by commas or hesitation (e.g. ', like,' or 'like, uh')
        - 'actually'/'basically': counted when used as introductory discourse filler (e.g. 'well, actually,')
        - 'so': counted as clause-leading hesitation (e.g. '^so,' or 'so, um')
    """
    if not text or not text.strip():
        return {}

    counts: Dict[str, int] = {}
    lower = text.lower()

    # 1. Unconditional single-word fillers
    unconditional_fillers = ["um", "uh", "er", "erm", "ah"]
    for filler in unconditional_fillers:
        matches = re.findall(rf"\b{filler}\b", lower)
        if matches:
            counts[filler] = len(matches)

    # 2. Multi-word phrase fillers
    multi_fillers = ["you know", "i mean"]
    for phrase in multi_fillers:
        matches = re.findall(rf"\b{re.escape(phrase)}\b", lower)
        if matches:
            counts[phrase] = len(matches)

    # 3. Contextual 'like' filler (e.g. ", like," or "like, uh" or "was, like,")
    # Does NOT match "I like Python" or "looks like"
    like_filler_matches = re.findall(
        r"(?:,\s*like\s*,|,\s*like\s+[a-z]+|\blike,\s*(?:um|uh|you know)|\bwas,\s*like\b)", lower
    )
    if like_filler_matches:
        counts["like"] = len(like_filler_matches)

    # 4. Contextual 'basically' & 'actually' discourse markers
    for marker in ["basically", "actually"]:
        marker_matches = re.findall(rf"(?:^\s*{marker}\s*,|,\s*{marker}\s*,|\bwell,\s*{marker}\b)", lower)
        if marker_matches:
            counts[marker] = len(marker_matches)

    # 5. Clause-initial filler 'so' (e.g., "So, um," or "^So, ")
    so_matches = re.findall(r"(?:^\s*so,\s*(?:um|uh|well|basically)?|\bso,\s*um\b)", lower)
    if so_matches:
        counts["so"] = len(so_matches)

    return counts


# ==============================================================================
# 3. Repetition Detection
# ==============================================================================

def detect_repetitions(texts: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Detect repeated meaningful words and 2-to-4-word phrases across user responses.
    Filters out common stop words to avoid noise.
    
    Returns:
        Tuple of (repeated_phrases, repeated_words).
    """
    combined = " ".join(texts).lower()
    words = re.findall(r"\b[a-z0-9'-]+\b", combined)

    # 1. Word frequency analysis (non-stop words with length > 2)
    word_freq: Dict[str, int] = {}
    for w in words:
        if w not in STOP_WORDS and len(w) > 2:
            word_freq[w] = word_freq.get(w, 0) + 1

    repeated_words = [
        {"word": w, "count": count}
        for w, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        if count >= 3
    ][:8]

    # 2. Phrase frequency analysis (2 to 4 n-grams)
    phrase_freq: Dict[str, int] = {}
    for n in range(2, 5):
        for i in range(len(words) - n + 1):
            ngram = words[i : i + n]
            # Ensure at least one word in the n-gram is a non-stop content word
            if any(w not in STOP_WORDS for w in ngram) and not all(w in STOP_WORDS for w in ngram):
                phrase = " ".join(ngram)
                phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 1

    repeated_phrases = [
        {"phrase": p, "count": count}
        for p, count in sorted(phrase_freq.items(), key=lambda x: x[1], reverse=True)
        if count >= 2
    ][:6]

    return repeated_phrases, repeated_words


# ==============================================================================
# 4. Question Extraction
# ==============================================================================

def extract_questions_from_text(text: str) -> List[str]:
    """
    Extract discrete questions from an assistant turn.
    Splits on sentence boundaries and identifies interrogative structures or question marks.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    questions: List[str] = []
    
    interrogative_starters = (
        "how", "why", "what", "could", "can", "would", "tell me", "explain",
        "describe", "where", "who", "when", "which", "are you", "do you", "is there"
    )

    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        if s_clean.endswith("?") or s_clean.lower().startswith(interrogative_starters):
            questions.append(s_clean)

    return questions


# ==============================================================================
# 5. Question Alignment Heuristic
# ==============================================================================

def assess_question_alignment(question: str, user_answer: str) -> str:
    """
    Heuristically assess whether a user answer addresses the preceding question.
    
    Returns:
        'addressed', 'partially_addressed', or 'unaddressed'.
    """
    if not user_answer or len(user_answer.strip().split()) < 4:
        return "unaddressed"

    q_words = {
        w.lower()
        for w in re.findall(r"\b[a-z]{3,}\b", question)
        if w.lower() not in STOP_WORDS
    }
    ans_words = {
        w.lower()
        for w in re.findall(r"\b[a-z]{3,}\b", user_answer)
        if w.lower() not in STOP_WORDS
    }

    if not q_words:
        return "addressed"

    overlap = q_words.intersection(ans_words)
    overlap_ratio = len(overlap) / len(q_words)

    if overlap_ratio >= 0.25 or len(user_answer.split()) >= 25:
        return "addressed"
    elif overlap_ratio > 0 or len(user_answer.split()) >= 10:
        return "partially_addressed"
    else:
        return "unaddressed"


# ==============================================================================
# 6. Potential Contradiction Detection
# ==============================================================================

def detect_potential_contradictions(user_texts: List[str]) -> List[str]:
    """
    Identify obvious potential inconsistencies across candidate turns.
    """
    combined_turns = [t.lower() for t in user_texts]
    contradictions: List[str] = []

    # Heuristic 1: Real-time vs Batch / Daily processing
    has_realtime = any("real-time" in t or "real time" in t or "stream" in t for t in combined_turns)
    has_batch = any("24 hours" in t or "daily batch" in t or "once a day" in t for t in combined_turns)
    if has_realtime and has_batch:
        contradictions.append(
            "Potential contradiction: Early statement referenced 'real-time / streaming' processing, "
            "while a subsequent statement mentioned 'daily / 24-hour batch' processing."
        )

    # Heuristic 2: Zero dependencies vs Complex cloud stack
    has_zero_deps = any("zero dependencies" in t or "standalone" in t or "no external library" in t for t in combined_turns)
    has_heavy_stack = any("kubernetes" in t or "redis cluster" in t or "distributed database" in t for t in combined_turns)
    if has_zero_deps and has_heavy_stack:
        contradictions.append(
            "Potential contradiction: Statement claimed 'zero external dependencies', "
            "yet subsequent answers referenced distributed infrastructure (Kubernetes/Redis)."
        )

    # Heuristic 3: 100% accuracy vs Non-deterministic model
    has_perfect_acc = any("100% accuracy" in t or "zero errors" in t or "flawless" in t for t in combined_turns)
    has_probabilistic = any("hallucination" in t or "probabilistic" in t or "error margin" in t for t in combined_turns)
    if has_perfect_acc and has_probabilistic:
        contradictions.append(
            "Potential contradiction: Claimed '100% accuracy / zero errors', "
            "while acknowledging 'probabilistic / hallucination' edge cases."
        )

    return contradictions
