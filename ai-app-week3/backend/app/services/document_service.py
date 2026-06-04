from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk
from app.schemas import DocumentIngestTextRequest, DocumentRechunkRequest
from app.services.document_chunk_service import split_text
from datetime import datetime


def _create_chunk_records(
    db: Session,
    document_id: int,
    chunks_data: List[Tuple[str, int, int]],
) -> List[DocumentChunk]:
    chunk_records: List[DocumentChunk] = []

    for index, (chunk_content, char_start, char_end) in enumerate(chunks_data):
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            content=chunk_content,
            char_start=char_start,
            char_end=char_end,
            is_active=True,
            quality_status="unknown",
        )
        db.add(chunk)
        chunk_records.append(chunk)

    db.commit()

    for chunk in chunk_records:
        db.refresh(chunk)

    return chunk_records


def create_document_with_chunks(
    db: Session,
    payload: DocumentIngestTextRequest,
) -> tuple[Document, list[DocumentChunk]]:
    chunks_data = split_text(
        text=payload.content,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        split_strategy=payload.split_strategy,
    )

    document = Document(
        title=payload.title,
        source_type=payload.split_strategy,
        content=payload.content,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        chunk_count=len(chunks_data),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    chunk_records = _create_chunk_records(
        db=db,
        document_id=document.id,
        chunks_data=chunks_data,
    )

    return document, chunk_records


def rechunk_document(
    db: Session,
    document: Document,
    payload: DocumentRechunkRequest,
) -> tuple[Document, list[DocumentChunk]]:
    chunks_data = split_text(
        text=document.content,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        split_strategy=payload.split_strategy,
    )

    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document.id
    ).delete(synchronize_session=False)

    document.source_type = payload.split_strategy
    document.chunk_size = payload.chunk_size
    document.chunk_overlap = payload.chunk_overlap
    document.chunk_count = len(chunks_data)

    db.add(document)
    db.commit()
    db.refresh(document)

    chunk_records = _create_chunk_records(
        db=db,
        document_id=document.id,
        chunks_data=chunks_data,
    )

    return document, chunk_records


def list_recent_documents(
    db: Session,
    limit: int = 20,
) -> list[Document]:
    safe_limit = min(max(limit, 1), 50)

    return (
        db.query(Document)
        .order_by(Document.id.desc())
        .limit(safe_limit)
        .all()
    )


def list_document_chunks(
    db: Session,
    document_id: int,
) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )


def get_document_by_id(
    db: Session,
    document_id: int,
) -> Optional[Document]:
    return (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

def search_document_chunks(
    db: Session,
    keyword: str,
    document_id: Optional[int] = None,
    limit: int = 20,
) -> list[dict]:
    safe_keyword = keyword.strip()
    safe_limit = min(max(limit, 1), 50)

    query = (
        db.query(DocumentChunk, Document)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(DocumentChunk.is_active.is_(True))
        .filter(DocumentChunk.content.contains(safe_keyword))
    )

    if document_id is not None:
        query = query.filter(DocumentChunk.document_id == document_id)

    rows = (
        query
        .order_by(DocumentChunk.id.desc())
        .limit(safe_limit)
        .all()
    )

    results: list[dict] = []

    for chunk, document in rows:
        results.append(
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "document_title": document.title,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
            "is_active": chunk.is_active,
            "quality_status": chunk.quality_status,
            "quality_note": chunk.quality_note,
            "created_at": chunk.created_at,
        }
    )

    return results

def get_document_chunk_by_id(
    db: Session,
    chunk_id: int,
) -> Optional[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.id == chunk_id)
        .first()
    )


def update_document_chunk(
    db: Session,
    chunk: DocumentChunk,
    content: str,
    is_active: bool,
    quality_status: str = "unknown",
    quality_note: str | None = None,
) -> DocumentChunk:
    chunk.content = content
    chunk.is_active = is_active
    chunk.quality_status = quality_status
    chunk.quality_note = quality_note
    chunk.updated_at = datetime.utcnow()

    db.add(chunk)
    db.commit()
    db.refresh(chunk)

    return chunk