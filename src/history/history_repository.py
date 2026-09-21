"""
SQLite Repository Layer for Pitch Practice Partner.
Provides persistent storage, querying, and retrieval for practice sessions,
conversation transcripts, dimensional scores, and explainable feedback.
"""

import os
import json
import sqlite3
from contextlib import contextmanager
from typing import List, Optional, Dict, Any, Generator

from src.history.history_models import (
    HistoricalSession,
    HistoricalMessage,
    HistoricalDimensionScore,
    evaluation_from_dict,
    feedback_from_dict,
    evaluation_to_dict,
    feedback_to_dict,
)

DEFAULT_DB_PATH = os.environ.get("PITCH_PRACTICE_DB_PATH", os.path.join("data", "pitch_practice.db"))


class HistoryRepository:
    """
    Encapsulates all SQLite interactions for persistent session history.
    Ensures safe schema initialization, parameterized queries, and graceful error handling.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the repository with a SQLite database path.
        Creates parent directories if necessary and sets up required tables.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self) -> None:
        """Create directory for the database file if it does not exist (skip for :memory:)."""
        if self.db_path != ":memory:":
            dirname = os.path.dirname(self.db_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Create a connection with foreign key enforcement and row factory.
        Ensures the connection is always closed so file locks are promptly released on Windows.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create schema tables and indices if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    scenario_name TEXT NOT NULL,
                    persona_id TEXT NOT NULL,
                    persona_name TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    turn_count INTEGER NOT NULL,
                    overall_score REAL NOT NULL,
                    max_score REAL NOT NULL DEFAULT 100.0,
                    duration_seconds REAL,
                    evaluation_status TEXT NOT NULL DEFAULT 'completed',
                    evaluation_json TEXT,
                    feedback_json TEXT
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    turn_order INTEGER NOT NULL,
                    timestamp TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS dimension_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    dimension_name TEXT NOT NULL,
                    score REAL,
                    max_score REAL DEFAULT 100.0,
                    weight REAL DEFAULT 1.0,
                    status TEXT NOT NULL,
                    evidence_json TEXT,
                    rationale TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_mode ON sessions(mode);
                CREATE INDEX IF NOT EXISTS idx_sessions_completed ON sessions(completed_at);
                CREATE INDEX IF NOT EXISTS idx_sessions_difficulty ON sessions(difficulty);
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_dimension_session ON dimension_scores(session_id);
                CREATE INDEX IF NOT EXISTS idx_dimension_name ON dimension_scores(dimension_name);
                """
            )
            conn.commit()

    def save_session(self, session: HistoricalSession) -> bool:
        """
        Save a historical session and its associated messages and dimension scores.
        Uses an atomic transaction with REPLACE semantics for idempotency.
        """
        try:
            eval_dict = evaluation_to_dict(session.evaluation) if session.evaluation else None
            feed_dict = feedback_to_dict(session.feedback) if session.feedback else None

            eval_json_str = json.dumps(eval_dict) if eval_dict is not None else session.raw_evaluation_json
            feed_json_str = json.dumps(feed_dict) if feed_dict is not None else session.raw_feedback_json

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO sessions (
                        session_id, created_at, completed_at, mode, scenario_id,
                        scenario_name, persona_id, persona_name, difficulty,
                        turn_count, overall_score, max_score, duration_seconds,
                        evaluation_status, evaluation_json, feedback_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        completed_at=excluded.completed_at,
                        turn_count=excluded.turn_count,
                        overall_score=excluded.overall_score,
                        duration_seconds=excluded.duration_seconds,
                        evaluation_status=excluded.evaluation_status,
                        evaluation_json=excluded.evaluation_json,
                        feedback_json=excluded.feedback_json;
                    """,
                    (
                        session.session_id,
                        session.created_at,
                        session.completed_at,
                        session.mode,
                        session.scenario_id,
                        session.scenario_name,
                        session.persona_id,
                        session.persona_name,
                        session.difficulty,
                        session.turn_count,
                        session.overall_score,
                        session.max_score,
                        session.duration_seconds,
                        session.evaluation_status,
                        eval_json_str,
                        feed_json_str,
                    ),
                )

                # Clear and re-insert messages & dimensions for consistency
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session.session_id,))
                cursor.execute("DELETE FROM dimension_scores WHERE session_id = ?", (session.session_id,))

                # Insert messages
                for msg in session.messages:
                    cursor.execute(
                        """
                        INSERT INTO messages (session_id, role, content, turn_order, timestamp)
                        VALUES (?, ?, ?, ?, ?);
                        """,
                        (session.session_id, msg.role, msg.content, msg.turn_order, msg.timestamp),
                    )

                # Insert dimension scores
                for dim in session.dimensions:
                    cursor.execute(
                        """
                        INSERT INTO dimension_scores (
                            session_id, dimension_name, score, max_score, weight, status, evidence_json, rationale
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            session.session_id,
                            dim.name,
                            dim.score,
                            dim.max_score,
                            dim.weight,
                            dim.status,
                            json.dumps(dim.evidence),
                            dim.rationale,
                        ),
                    )

                conn.commit()
                return True
        except Exception:
            return False

    def get_session(self, session_id: str) -> Optional[HistoricalSession]:
        """
        Retrieve a complete HistoricalSession by its session_id.
        Returns None if not found or if row cannot be loaded.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT session_id, created_at, completed_at, mode, scenario_id,
                           scenario_name, persona_id, persona_name, difficulty,
                           turn_count, overall_score, max_score, duration_seconds,
                           evaluation_status, evaluation_json, feedback_json
                    FROM sessions
                    WHERE session_id = ?;
                    """,
                    (session_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return None

                # Fetch messages
                cursor.execute(
                    """
                    SELECT role, content, turn_order, timestamp
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY turn_order ASC;
                    """,
                    (session_id,),
                )
                msg_rows = cursor.fetchall()
                messages = [
                    HistoricalMessage(
                        role=m["role"],
                        content=m["content"],
                        turn_order=m["turn_order"],
                        timestamp=m["timestamp"],
                    )
                    for m in msg_rows
                ]

                # Fetch dimension scores
                cursor.execute(
                    """
                    SELECT dimension_name, score, max_score, weight, status, evidence_json, rationale
                    FROM dimension_scores
                    WHERE session_id = ?
                    ORDER BY id ASC;
                    """,
                    (session_id,),
                )
                dim_rows = cursor.fetchall()
                dimensions = []
                for d in dim_rows:
                    evidence_list = []
                    if d["evidence_json"]:
                        try:
                            evidence_list = json.loads(d["evidence_json"])
                        except Exception:
                            evidence_list = []
                    dimensions.append(
                        HistoricalDimensionScore(
                            name=d["dimension_name"],
                            score=d["score"],
                            max_score=d["max_score"] or 100.0,
                            weight=d["weight"] or 1.0,
                            status=d["status"] or "evaluated",
                            evidence=evidence_list,
                            rationale=d["rationale"] or "",
                        )
                    )

                # Parse evaluation and feedback objects
                eval_obj = None
                if row["evaluation_json"]:
                    try:
                        eval_data = json.loads(row["evaluation_json"])
                        eval_obj = evaluation_from_dict(eval_data)
                    except Exception:
                        eval_obj = None

                feedback_obj = None
                if row["feedback_json"]:
                    try:
                        feed_data = json.loads(row["feedback_json"])
                        feedback_obj = feedback_from_dict(feed_data)
                    except Exception:
                        feedback_obj = None

                return HistoricalSession(
                    session_id=row["session_id"],
                    created_at=row["created_at"],
                    completed_at=row["completed_at"],
                    mode=row["mode"],
                    scenario_id=row["scenario_id"],
                    scenario_name=row["scenario_name"],
                    persona_id=row["persona_id"],
                    persona_name=row["persona_name"],
                    difficulty=row["difficulty"],
                    turn_count=row["turn_count"],
                    overall_score=row["overall_score"],
                    max_score=row["max_score"] or 100.0,
                    duration_seconds=row["duration_seconds"],
                    evaluation_status=row["evaluation_status"] or "completed",
                    messages=messages,
                    dimensions=dimensions,
                    evaluation=eval_obj,
                    feedback=feedback_obj,
                    raw_evaluation_json=row["evaluation_json"],
                    raw_feedback_json=row["feedback_json"],
                )
        except Exception:
            return None

    def list_sessions(
        self,
        mode: Optional[str] = None,
        difficulty: Optional[str] = None,
        scenario_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        order_by: str = "completed_at DESC",
    ) -> List[HistoricalSession]:
        """
        Query completed sessions with optional filters.
        Orders results safely using allowed order_by clauses.
        """
        allowed_orders = {
            "completed_at DESC": "completed_at DESC",
            "completed_at ASC": "completed_at ASC",
            "overall_score DESC": "overall_score DESC",
            "overall_score ASC": "overall_score ASC",
        }
        order_clause = allowed_orders.get(order_by, "completed_at DESC")

        query = """
            SELECT session_id, created_at, completed_at, mode, scenario_id,
                   scenario_name, persona_id, persona_name, difficulty,
                   turn_count, overall_score, max_score, duration_seconds,
                   evaluation_status, evaluation_json, feedback_json
            FROM sessions
            WHERE 1=1
        """
        params: List[Any] = []

        if mode and mode != "All":
            query += " AND mode = ?"
            params.append(mode)

        if difficulty and difficulty != "All":
            query += " AND difficulty = ?"
            params.append(difficulty)

        if scenario_id:
            query += " AND scenario_id = ?"
            params.append(scenario_id)

        if start_date:
            query += " AND completed_at >= ?"
            params.append(start_date)

        if end_date:
            query += " AND completed_at <= ?"
            params.append(end_date)

        if min_score is not None:
            query += " AND overall_score >= ?"
            params.append(min_score)

        if max_score is not None:
            query += " AND overall_score <= ?"
            params.append(max_score)

        query += f" ORDER BY {order_clause};"

        results: List[HistoricalSession] = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()
                for row in rows:
                    session = self.get_session(row["session_id"])
                    if session:
                        results.append(session)
        except Exception:
            return []

        return results

    def delete_session(self, session_id: str) -> bool:
        """
        Permanently delete a session record, cascade deleting messages and dimensions.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

    def count_sessions(
        self,
        mode: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> int:
        """Count total completed sessions matching optional mode or difficulty."""
        try:
            query = "SELECT COUNT(*) AS total FROM sessions WHERE 1=1"
            params: List[Any] = []

            if mode and mode != "All":
                query += " AND mode = ?"
                params.append(mode)

            if difficulty and difficulty != "All":
                query += " AND difficulty = ?"
                params.append(difficulty)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                row = cursor.fetchone()
                return int(row["total"]) if row else 0
        except Exception:
            return 0

    def clear_all_sessions(self) -> int:
        """Clear all historical session data (used for testing or maintenance)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages;")
                cursor.execute("DELETE FROM dimension_scores;")
                cursor.execute("DELETE FROM sessions;")
                conn.commit()
                return cursor.rowcount
        except Exception:
            return 0
