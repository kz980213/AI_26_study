from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk, ChunkEmbedding


def _is_chunk_active(chunk: DocumentChunk) -> bool:
    if hasattr(chunk, "is_active"):
        return bool(chunk.is_active)

    if hasattr(chunk, "status"):
        return getattr(chunk, "status") == "active"

    return True


def _get_document_title(document: Document) -> str:
    for field_name in ["title", "name", "filename", "file_name"]:
        value = getattr(document, field_name, None)
        if value:
            return value

    return f"Document #{document.id}"


def _get_chunk_content(chunk: DocumentChunk) -> str:
    for field_name in ["content", "text", "chunk_text"]:
        value = getattr(chunk, field_name, None)
        if value:
            return value

    return ""


def get_embedding_stats(db: Session) -> dict[str, Any]:
    documents = db.query(Document).order_by(Document.id.desc()).all()
    chunks = db.query(DocumentChunk).all()
    embeddings = db.query(ChunkEmbedding).all()

    embedded_chunk_ids = {item.chunk_id for item in embeddings}

    total_chunks = len(chunks)
    active_chunks = [chunk for chunk in chunks if _is_chunk_active(chunk)]
    active_chunk_ids = {chunk.id for chunk in active_chunks}

    embedded_active_chunk_ids = active_chunk_ids.intersection(embedded_chunk_ids)

    active_chunk_count = len(active_chunks)
    embedded_active_chunk_count = len(embedded_active_chunk_ids)
    missing_active_chunk_count = active_chunk_count - embedded_active_chunk_count

    coverage_rate = (
        round(embedded_active_chunk_count / active_chunk_count * 100, 2)
        if active_chunk_count > 0
        else 0
    )

    document_items = []

    for document in documents:
        document_chunks = [
            chunk
            for chunk in chunks
            if getattr(chunk, "document_id", None) == document.id
        ]

        document_active_chunks = [
            chunk for chunk in document_chunks if _is_chunk_active(chunk)
        ]

        document_active_chunk_ids = {chunk.id for chunk in document_active_chunks}
        document_embedded_active_ids = document_active_chunk_ids.intersection(
            embedded_chunk_ids
        )

        document_active_count = len(document_active_chunks)
        document_embedded_count = len(document_embedded_active_ids)
        document_missing_count = document_active_count - document_embedded_count

        document_coverage_rate = (
            round(document_embedded_count / document_active_count * 100, 2)
            if document_active_count > 0
            else 0
        )

        document_items.append(
            {
                "document_id": document.id,
                "title": _get_document_title(document),
                "total_chunks": len(document_chunks),
                "active_chunks": document_active_count,
                "embedded_active_chunks": document_embedded_count,
                "missing_active_chunks": document_missing_count,
                "coverage_rate": document_coverage_rate,
            }
        )

    return {
        "total_documents": len(documents),
        "total_chunks": total_chunks,
        "active_chunks": active_chunk_count,
        "embedding_records": len(embeddings),
        "embedded_active_chunks": embedded_active_chunk_count,
        "missing_active_chunks": missing_active_chunk_count,
        "coverage_rate": coverage_rate,
        "documents": document_items,
    }


def list_missing_embedding_chunks(
    db: Session,
    document_id: Optional[int] = None,
    limit: int = 50,
) -> dict[str, Any]:
    limit = min(max(limit, 1), 200)

    chunks_query = db.query(DocumentChunk)

    if document_id is not None:
        chunks_query = chunks_query.filter(DocumentChunk.document_id == document_id)

    chunks = chunks_query.order_by(DocumentChunk.id.asc()).all()

    embedded_chunk_ids = {
        item.chunk_id
        for item in db.query(ChunkEmbedding.chunk_id).all()
    }

    missing_items = []

    for chunk in chunks:
        if not _is_chunk_active(chunk):
            continue

        if chunk.id in embedded_chunk_ids:
            continue

        content = _get_chunk_content(chunk)

        missing_items.append(
            {
                "chunk_id": chunk.id,
                "document_id": getattr(chunk, "document_id", None),
                "content_preview": content[:160],
                "quality_status": getattr(chunk, "quality_status", None),
                "quality_note": getattr(chunk, "quality_note", None),
                "is_active": getattr(chunk, "is_active", None),
                "status": getattr(chunk, "status", None),
            }
        )

        if len(missing_items) >= limit:
            break

    return {
        "document_id": document_id,
        "limit": limit,
        "missing_count": len(missing_items),
        "items": missing_items,
    }