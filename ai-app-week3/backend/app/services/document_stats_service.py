from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk


def get_document_stats(db: Session) -> dict:
    total_documents = db.query(Document).count()
    total_chunks = db.query(DocumentChunk).count()

    active_chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.is_active.is_(True))
        .count()
    )

    inactive_chunks = total_chunks - active_chunks

    quality_counts = {
        "unknown": 0,
        "good": 0,
        "needs_review": 0,
        "bad": 0,
    }

    rows = (
        db.query(
            DocumentChunk.quality_status,
            func.count(DocumentChunk.id),
        )
        .group_by(DocumentChunk.quality_status)
        .all()
    )

    for status, count in rows:
        quality_counts[status or "unknown"] = count

    if total_documents == 0:
        average_chunks_per_document = 0.0
    else:
        average_chunks_per_document = round(
            total_chunks / total_documents,
            2,
        )

    latest_document = (
        db.query(Document)
        .order_by(Document.id.desc())
        .first()
    )

    return {
        "total_documents": total_documents,
        "total_chunks": total_chunks,
        "active_chunks": active_chunks,
        "inactive_chunks": inactive_chunks,
        "quality_counts": quality_counts,
        "average_chunks_per_document": average_chunks_per_document,
        "latest_document": latest_document,
    }