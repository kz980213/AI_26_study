from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk
from app.schemas import DocumentIngestTextRequest
from app.services.document_chunk_service import split_text_by_chars


def create_document_with_chunks(
    db: Session,
    payload: DocumentIngestTextRequest,
) -> tuple[Document, list[DocumentChunk]]:
    chunks_data = split_text_by_chars(
        text=payload.content,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
    )

    document = Document(
        title=payload.title,
        source_type="text",
        content=payload.content,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        chunk_count=len(chunks_data),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    chunk_records: list[DocumentChunk] = []

    for index, (chunk_content, char_start, char_end) in enumerate(chunks_data):
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            content=chunk_content,
            char_start=char_start,
            char_end=char_end,
        )
        db.add(chunk)
        chunk_records.append(chunk)

    db.commit()

    for chunk in chunk_records:
        db.refresh(chunk)

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
) -> Document | None:
    return (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )