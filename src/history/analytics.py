"""
Analytics and Longitudinal Performance Tracking for Pitch Practice Partner.
Computes descriptive statistics, chronological progress, dimensional averages,
recurring strength/improvement patterns, and neutral two-session comparisons.
"""

from collections import Counter
from typing import List, Dict, Any, Optional
from src.history.history_models import HistoricalSession
from src.history.history_service import HistoryService


class AnalyticsService:
    """
    Computes objective, descriptive analytics across historical sessions.
    Strictly avoids psychological, personality, or non-verifiable diagnoses.
    """

    def __init__(self, history_service: HistoryService):
        """Initialize with an active HistoryService."""
        self.history_service = history_service

    def get_sessions(
        self,
        mode: Optional[str] = None,
        difficulty: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[HistoricalSession]:
        """Fetch historical sessions matching specified filters."""
        return self.history_service.list_sessions(
            mode=mode,
            difficulty=difficulty,
            start_date=start_date,
            end_date=end_date,
            order_by="completed_at ASC",
        )

    def get_overall_summary(self, sessions: Optional[List[HistoricalSession]] = None) -> Dict[str, Any]:
        """
        Compute high-level descriptive summary statistics.
        Uses neutral descriptive terminology (e.g., 'Highest recorded score').
        """
        if sessions is None:
            sessions = self.get_sessions()

        if not sessions:
            return {
                "total_sessions": 0,
                "average_score": 0.0,
                "highest_recorded_score": 0.0,
                "lowest_recorded_score": 0.0,
                "average_turns": 0.0,
                "total_turns": 0,
                "average_duration_seconds": 0.0,
                "has_sufficient_data": False,
            }

        scores = [s.overall_score for s in sessions]
        turns = [s.turn_count for s in sessions]
        durations = [s.duration_seconds for s in sessions if s.duration_seconds is not None]

        avg_score = sum(scores) / len(scores)
        avg_turns = sum(turns) / len(turns)
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total_sessions": len(sessions),
            "average_score": round(avg_score, 1),
            "highest_recorded_score": round(max(scores), 1),
            "lowest_recorded_score": round(min(scores), 1),
            "average_turns": round(avg_turns, 1),
            "total_turns": sum(turns),
            "average_duration_seconds": round(avg_duration, 1),
            "has_sufficient_data": True,
        }

    def get_chronological_progress(
        self, sessions: Optional[List[HistoricalSession]] = None
    ) -> List[Dict[str, Any]]:
        """
        Produce chronological performance records for longitudinal charting.
        Sorted from earliest to most recent completed session.
        """
        if sessions is None:
            sessions = self.get_sessions()

        # Sort chronologically by completed_at
        sorted_sessions = sorted(sessions, key=lambda s: s.completed_at)

        progress: List[Dict[str, Any]] = []
        for idx, s in enumerate(sorted_sessions, start=1):
            progress.append(
                {
                    "session_number": idx,
                    "session_id": s.session_id,
                    "date": s.formatted_date,
                    "timestamp": s.completed_at,
                    "mode": s.mode,
                    "scenario": s.scenario_name,
                    "difficulty": s.difficulty,
                    "score": round(s.overall_score, 1),
                    "turns": s.turn_count,
                }
            )
        return progress

    def get_mode_breakdown(
        self, sessions: Optional[List[HistoricalSession]] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate descriptive statistics broken down by practice mode.
        Neutral descriptive metrics without value judgments like 'best' or 'worst'.
        """
        if sessions is None:
            sessions = self.get_sessions()

        mode_groups: Dict[str, List[HistoricalSession]] = {}
        for s in sessions:
            mode_groups.setdefault(s.mode, []).append(s)

        breakdown: List[Dict[str, Any]] = []
        for mode, group in sorted(mode_groups.items()):
            scores = [s.overall_score for s in group]
            avg_score = sum(scores) / len(scores)
            breakdown.append(
                {
                    "mode": mode,
                    "session_count": len(group),
                    "average_score": round(avg_score, 1),
                    "highest_score": round(max(scores), 1),
                    "lowest_score": round(min(scores), 1),
                }
            )
        return breakdown

    def get_difficulty_breakdown(
        self, sessions: Optional[List[HistoricalSession]] = None
    ) -> List[Dict[str, Any]]:
        """Calculate descriptive metrics by difficulty level."""
        if sessions is None:
            sessions = self.get_sessions()

        diff_groups: Dict[str, List[HistoricalSession]] = {}
        for s in sessions:
            diff_groups.setdefault(s.difficulty, []).append(s)

        breakdown: List[Dict[str, Any]] = []
        # Standard difficulty ordering
        order = ["Beginner", "Intermediate", "Advanced"]
        for diff in order:
            if diff in diff_groups:
                group = diff_groups[diff]
                scores = [s.overall_score for s in group]
                avg_score = sum(scores) / len(scores)
                breakdown.append(
                    {
                        "difficulty": diff,
                        "session_count": len(group),
                        "average_score": round(avg_score, 1),
                        "highest_score": round(max(scores), 1),
                        "lowest_score": round(min(scores), 1),
                    }
                )
        return breakdown

    def get_dimension_averages(
        self, sessions: Optional[List[HistoricalSession]] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate descriptive historical averages for evaluated dimensions.
        Omits dimensions with insufficient evidence or un-scored records.
        """
        if sessions is None:
            sessions = self.get_sessions()

        dim_scores: Dict[str, List[float]] = {}
        for s in sessions:
            for d in s.dimensions:
                if d.is_evaluated() and d.score is not None:
                    dim_scores.setdefault(d.name, []).append(d.score)

        results: List[Dict[str, Any]] = []
        for name, scores in sorted(dim_scores.items()):
            avg_score = sum(scores) / len(scores)
            results.append(
                {
                    "dimension": name,
                    "average_score": round(avg_score, 1),
                    "evaluations_count": len(scores),
                    "highest_score": round(max(scores), 1),
                    "lowest_score": round(min(scores), 1),
                }
            )
        return results

    def get_recurring_improvements(
        self, sessions: Optional[List[HistoricalSession]] = None, top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Identify recurring improvement themes across stored sessions.
        Uses structured Phase 6 improvement feedback or Phase 5 improvement areas.
        """
        if sessions is None:
            sessions = self.get_sessions()

        theme_counter: Counter[str] = Counter()
        for s in sessions:
            if s.feedback and s.feedback.improvements:
                for imp in s.feedback.improvements:
                    if imp.title:
                        theme_counter[imp.title] += 1
            elif s.evaluation and s.evaluation.improvement_areas:
                for area in s.evaluation.improvement_areas:
                    # Clean title if bullet or formatted
                    clean = area.lstrip("•- \t").split(":")[0].strip()
                    if clean:
                        theme_counter[clean] += 1

        results = []
        for theme, count in theme_counter.most_common(top_n):
            results.append(
                {
                    "theme": theme,
                    "occurrences": count,
                    "percentage": round((count / len(sessions)) * 100, 1) if sessions else 0.0,
                    "description": f"Appeared across {count} practice session{'s' if count != 1 else ''}.",
                }
            )
        return results

    def get_recurring_strengths(
        self, sessions: Optional[List[HistoricalSession]] = None, top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Identify frequently observed evidence-backed strengths across sessions.
        """
        if sessions is None:
            sessions = self.get_sessions()

        strength_counter: Counter[str] = Counter()
        for s in sessions:
            if s.feedback and s.feedback.strengths:
                for st in s.feedback.strengths:
                    if st.title:
                        strength_counter[st.title] += 1
            elif s.evaluation and s.evaluation.strengths:
                for st_text in s.evaluation.strengths:
                    clean = st_text.lstrip("•- \t").split(":")[0].strip()
                    if clean:
                        strength_counter[clean] += 1

        results = []
        for title, count in strength_counter.most_common(top_n):
            results.append(
                {
                    "strength": title,
                    "occurrences": count,
                    "percentage": round((count / len(sessions)) * 100, 1) if sessions else 0.0,
                    "description": f"Demonstrated in {count} practice session{'s' if count != 1 else ''}.",
                }
            )
        return results


def compare_sessions(
    session_a: HistoricalSession,
    session_b: HistoricalSession,
) -> Dict[str, Any]:
    """
    Compare two historical sessions side-by-side using neutral, descriptive language.
    Strictly avoids value judgments (no 'Session A was superior').
    
    Returns:
        Dict containing metadata comparison, score differences, dimensional comparisons,
        and common/distinct strengths and improvements.
    """
    score_diff = round(session_b.overall_score - session_a.overall_score, 1)
    if score_diff != 0:
        score_desc = f"Recorded score difference: {score_diff:+.1f} points."
    else:
        score_desc = "Recorded score difference: 0.0 points (identical scores)."

    # Turn count diff
    turn_diff = session_b.turn_count - session_a.turn_count

    # Dimension comparison
    dims_a = {d.name: d for d in session_a.dimensions}
    dims_b = {d.name: d for d in session_b.dimensions}
    all_dim_names = sorted(set(dims_a.keys()).union(set(dims_b.keys())))

    dim_comparisons = []
    for dim_name in all_dim_names:
        da = dims_a.get(dim_name)
        db = dims_b.get(dim_name)

        score_a = da.score if da and da.is_evaluated() else None
        score_b = db.score if db and db.is_evaluated() else None

        if score_a is not None and score_b is not None:
            diff = round(score_b - score_a, 1)
            diff_str = f"{diff:+.1f}" if diff != 0 else "0.0"
        else:
            diff = None
            diff_str = "N/A"

        dim_comparisons.append(
            {
                "dimension": dim_name,
                "score_a": score_a,
                "score_b": score_b,
                "difference": diff,
                "difference_display": diff_str,
                "status_a": da.status if da else "not_present",
                "status_b": db.status if db else "not_present",
            }
        )

    # Extract strength titles
    strengths_a = set()
    if session_a.feedback and session_a.feedback.strengths:
        strengths_a = {s.title for s in session_a.feedback.strengths}
    elif session_a.evaluation:
        strengths_a = {s.lstrip("•- \t").split(":")[0].strip() for s in session_a.evaluation.strengths}

    strengths_b = set()
    if session_b.feedback and session_b.feedback.strengths:
        strengths_b = {s.title for s in session_b.feedback.strengths}
    elif session_b.evaluation:
        strengths_b = {s.lstrip("•- \t").split(":")[0].strip() for s in session_b.evaluation.strengths}

    common_strengths = sorted(strengths_a.intersection(strengths_b))
    distinct_a_strengths = sorted(strengths_a - strengths_b)
    distinct_b_strengths = sorted(strengths_b - strengths_a)

    # Extract improvement titles
    imp_a = set()
    if session_a.feedback and session_a.feedback.improvements:
        imp_a = {i.title for i in session_a.feedback.improvements}
    elif session_a.evaluation:
        imp_a = {i.lstrip("•- \t").split(":")[0].strip() for i in session_a.evaluation.improvement_areas}

    imp_b = set()
    if session_b.feedback and session_b.feedback.improvements:
        imp_b = {i.title for i in session_b.feedback.improvements}
    elif session_b.evaluation:
        imp_b = {i.lstrip("•- \t").split(":")[0].strip() for i in session_b.evaluation.improvement_areas}

    common_improvements = sorted(imp_a.intersection(imp_b))
    distinct_a_improvements = sorted(imp_a - imp_b)
    distinct_b_improvements = sorted(imp_b - imp_a)

    return {
        "session_a": {
            "session_id": session_a.session_id,
            "date": session_a.formatted_date,
            "mode": session_a.mode,
            "scenario": session_a.scenario_name,
            "persona": session_a.persona_name,
            "difficulty": session_a.difficulty,
            "turn_count": session_a.turn_count,
            "duration": session_a.formatted_duration,
            "overall_score": round(session_a.overall_score, 1),
        },
        "session_b": {
            "session_id": session_b.session_id,
            "date": session_b.formatted_date,
            "mode": session_b.mode,
            "scenario": session_b.scenario_name,
            "persona": session_b.persona_name,
            "difficulty": session_b.difficulty,
            "turn_count": session_b.turn_count,
            "duration": session_b.formatted_duration,
            "overall_score": round(session_b.overall_score, 1),
        },
        "overall_score_difference": score_diff,
        "overall_score_description": score_desc,
        "turn_difference": turn_diff,
        "dimension_comparisons": dim_comparisons,
        "common_strengths": common_strengths,
        "distinct_a_strengths": distinct_a_strengths,
        "distinct_b_strengths": distinct_b_strengths,
        "common_improvements": common_improvements,
        "distinct_a_improvements": distinct_a_improvements,
        "distinct_b_improvements": distinct_b_improvements,
    }
