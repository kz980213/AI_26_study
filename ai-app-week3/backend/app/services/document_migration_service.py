from sqlalchemy import text
from sqlalchemy.orm import Session


def ensure_document_chunk_manage_columns(db: Session) -> None:
    """
    SQLite 轻量迁移：
    给已经存在的 document_chunks 表补充管理字段。

    Base.metadata.create_all 只会创建不存在的表，
    不会给已存在的表自动加新列。
    """
    rows = db.execute(text("PRAGMA table_info(document_chunks)")).fetchall()
    column_names = {row[1] for row in rows}

    if "is_active" not in column_names:
        db.execute(
            text(
                "ALTER TABLE document_chunks "
                "ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"
            )
        )

    if "updated_at" not in column_names:
        db.execute(
            text(
                "ALTER TABLE document_chunks "
                "ADD COLUMN updated_at DATETIME"
            )
        )

    if "quality_status" not in column_names:
        db.execute(
            text(
                "ALTER TABLE document_chunks "
                "ADD COLUMN quality_status VARCHAR(30) NOT NULL DEFAULT 'unknown'"
            )
        )

    if "quality_note" not in column_names:
        db.execute(
            text(
                "ALTER TABLE document_chunks "
                "ADD COLUMN quality_note TEXT"
            )
        )

    db.commit()