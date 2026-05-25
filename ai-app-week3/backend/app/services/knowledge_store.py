import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "app.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_knowledge_tables():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                source_path TEXT NOT NULL UNIQUE,
                file_type TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                chunk_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                char_count INTEGER NOT NULL,
                meta_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_id) REFERENCES knowledge_documents(id)
            )
            """
        )
        conn.commit()


def delete_document_by_path(source_path: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM knowledge_documents WHERE source_path = ?",
            (source_path,),
        ).fetchone()

        if row:
            document_id = row["id"]
            conn.execute("DELETE FROM knowledge_chunks WHERE document_id = ?", (document_id,))
            conn.execute("DELETE FROM knowledge_documents WHERE id = ?", (document_id,))
            conn.commit()


def save_document_with_chunks(
    source_name: str,
    source_path: str,
    file_type: str,
    raw_text: str,
    chunks: List[Dict[str, Any]],
) -> int:
    delete_document_by_path(source_path)

    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO knowledge_documents (source_name, source_path, file_type, raw_text, chunk_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (source_name, source_path, file_type, raw_text, len(chunks)),
        )
        document_id = cursor.lastrowid

        for item in chunks:
            conn.execute(
                """
                INSERT INTO knowledge_chunks (document_id, chunk_index, content, char_count, meta_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    item["chunk_index"],
                    item["content"],
                    item["char_count"],
                    json.dumps(item.get("meta", {}), ensure_ascii=False),
                ),
            )

        conn.commit()

    return document_id


def list_documents(limit: int = 10):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, source_name, source_path, file_type, chunk_count, created_at
            FROM knowledge_documents
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def list_chunks(document_id: int, limit: int = 50):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, document_id, chunk_index, content, char_count, meta_json, created_at
            FROM knowledge_chunks
            WHERE document_id = ?
            ORDER BY chunk_index ASC
            LIMIT ?
            """,
            (document_id, limit),
        ).fetchall()

    result = []
    for row in rows:
        item = dict(row)
        item["meta_json"] = json.loads(item["meta_json"]) if item["meta_json"] else None
        result.append(item)
    return result