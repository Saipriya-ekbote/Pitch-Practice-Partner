"""
History and Analytics Package for Pitch Practice Partner.
Provides persistent storage, session reconstruction, and longitudinal analytics.
"""

from src.history.history_models import (
    HistoricalSession,
    HistoricalMessage,
    HistoricalDimensionScore,
    evaluation_from_dict,
    feedback_from_dict,
    evaluation_to_dict,
    feedback_to_dict,
)
from src.history.history_repository import (
    HistoryRepository,
    DEFAULT_DB_PATH,
)
from src.history.history_service import (
    HistoryService,
    calculate_session_duration,
)
from src.history.analytics import (
    AnalyticsService,
    compare_sessions,
)

__all__ = [
    "HistoricalSession",
    "HistoricalMessage",
    "HistoricalDimensionScore",
    "evaluation_from_dict",
    "feedback_from_dict",
    "evaluation_to_dict",
    "feedback_to_dict",
    "HistoryRepository",
    "DEFAULT_DB_PATH",
    "HistoryService",
    "calculate_session_duration",
    "AnalyticsService",
    "compare_sessions",
]
