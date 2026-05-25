import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "app.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_ai_task_table():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_task_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT NOT NULL,
                result_json TEXT NOT NULL,
                usage_json TEXT,
                model_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_ai_task_record(
    source_text: str,
    result_json: Dict[str, Any],
    usage: Optional[Dict[str, Any]] = None,
    model_name: str = ""
) -> int:
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO ai_task_records (source_text, result_json, usage_json, model_name)
            VALUES (?, ?, ?, ?)
            """,
            (
                source_text,
                json.dumps(result_json, ensure_ascii=False),
                json.dumps(usage, ensure_ascii=False) if usage else None,
                model_name,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def list_ai_task_records(limit: int = 10) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, source_text, result_json, usage_json, model_name, created_at
            FROM ai_task_records
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    result = []
    for row in rows:
        result.append(
            {
                "id": row["id"],
                "source_text": row["source_text"],
                "result_json": json.loads(row["result_json"]),
                "usage_json": json.loads(row["usage_json"]) if row["usage_json"] else None,
                "model_name": row["model_name"],
                "created_at": row["created_at"],
            }
        )
    return result