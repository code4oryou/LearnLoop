
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "learnloop.db"


def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                attempt INTEGER NOT NULL,
                approved INTEGER NOT NULL,
                checks_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                approved INTEGER NOT NULL,
                attempts INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_evaluation(topic, attempt, approved, checks):
    with connect() as db:
        db.execute(
            """
            INSERT INTO evaluations
            (topic, attempt, approved, checks_json)
            VALUES (?, ?, ?, ?)
            """,
            (topic, attempt, int(approved), json.dumps(checks))
        )


def save_lesson(topic, content, approved, attempts):
    with connect() as db:
        db.execute(
            """
            INSERT INTO lessons
            (topic, content, approved, attempts)
            VALUES (?, ?, ?, ?)
            """,
            (topic, content, int(approved), attempts)
        )


def recent_failures(topic, limit=5):
    with connect() as db:
        rows = db.execute(
            """
            SELECT attempt, checks_json
            FROM evaluations
            WHERE topic = ? AND approved = 0
            ORDER BY id DESC
            LIMIT ?
            """,
            (topic, limit)
        ).fetchall()

    return [
        {
            "attempt": row[0],
            "checks": json.loads(row[1])
        }
        for row in rows
    ]


def recent_lessons(limit=10):
    with connect() as db:
        return db.execute(
            """
            SELECT topic, approved, attempts, created_at
            FROM lessons
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
