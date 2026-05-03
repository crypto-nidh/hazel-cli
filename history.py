"""
history.py — Command History & Learning System
-----------------------------------------------
Stores every executed command in a local SQLite database (hazel.db).
Tracks frequency, timestamps, and session data.
"""

import sqlite3
import os
from datetime import datetime

# Database lives in the same directory as the scripts
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hazel.db')


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist. Called once at startup."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS commands (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT    NOT NULL,
            command         TEXT    NOT NULL,
            timestamp       TEXT    NOT NULL,
            tool            TEXT,
            was_blocked     INTEGER DEFAULT 0,
            output_snippet  TEXT
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            started_at  TEXT NOT NULL,
            ended_at    TEXT,
            note        TEXT
        );
    """)
    conn.commit()
    conn.close()


def start_session(session_id: str):
    conn = _get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO sessions (id, started_at) VALUES (?, ?)",
        (session_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def end_session(session_id: str):
    conn = _get_connection()
    conn.execute(
        "UPDATE sessions SET ended_at = ? WHERE id = ?",
        (datetime.now().isoformat(), session_id)
    )
    conn.commit()
    conn.close()


def save_command(session_id: str, command: str, tool: str = None,
                 was_blocked: bool = False, output_snippet: str = None):
    """Save an executed command to the database."""
    conn = _get_connection()
    conn.execute(
        """INSERT INTO commands
           (session_id, command, timestamp, tool, was_blocked, output_snippet)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            command,
            datetime.now().isoformat(),
            tool,
            1 if was_blocked else 0,
            output_snippet
        )
    )
    conn.commit()
    conn.close()


def get_session_commands(session_id: str) -> list:
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM commands WHERE session_id = ? ORDER BY timestamp",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_frequent_commands(limit: int = 10) -> list:
    conn = _get_connection()
    rows = conn.execute(
        """SELECT command, COUNT(*) as count
           FROM commands
           WHERE was_blocked = 0
           GROUP BY command
           ORDER BY count DESC
           LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_frequent_tools(limit: int = 5) -> list:
    conn = _get_connection()
    rows = conn.execute(
        """SELECT tool, COUNT(*) as count
           FROM commands
           WHERE tool IS NOT NULL AND was_blocked = 0
           GROUP BY tool
           ORDER BY count DESC
           LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_history(keyword: str, limit: int = 20) -> list:
    conn = _get_connection()
    rows = conn.execute(
        """SELECT * FROM commands
           WHERE command LIKE ?
           ORDER BY timestamp DESC
           LIMIT ?""",
        (f"%{keyword}%", limit)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_last_n_commands(n: int = 20) -> list:
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM commands ORDER BY timestamp DESC LIMIT ?", (n,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]