"""Audit log storage using SQLite for remediation history."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "audit_log.db"


def _get_conn():
    """Get a SQLite connection, creating the table if needed."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            issue_id TEXT,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            details TEXT
        )
    """)
    conn.commit()
    return conn


def log_action(issue_id: str, action: str, status: str, message: str = "", details: dict | None = None):
    """Log a remediation action to the audit database."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO audit_log (timestamp, issue_id, action, status, message, details) VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now().isoformat(),
                issue_id,
                action,
                status,
                message,
                json.dumps(details) if details else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_audit_log(limit: int = 100) -> list[dict]:
    """Retrieve recent audit log entries."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "SELECT id, timestamp, issue_id, action, status, message, details FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "issue_id": row[2],
                "action": row[3],
                "status": row[4],
                "message": row[5],
                "details": json.loads(row[6]) if row[6] else None,
            }
            for row in rows
        ]
    finally:
        conn.close()
