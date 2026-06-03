from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    DocumentChunkListResponse,
    DocumentIngestTextRequest,
    DocumentIngestTextResponse,
    DocumentListResponse,
)
from app.services.document_service import (
    create_document_with_chunks,
    get_document_by_id,
    list_document_chunks,
    list_recent_documents,
)

router = APIRouter(
    prefix="/ai/documents",
    tags=["documents"],
)


@router.post(
    "/ingest-text",
    response_model=DocumentIngestTextResponse,
)
def ingest_text_document(
    payload: DocumentIngestTextRequest,
    db: Session = Depends(get_db),
):
    if payload.chunk_overlap >= payload.chunk_size:
        raise HTTPException(
            status_code=400,
            detail="chunk_overlap 必须小于 chunk_size",
        )

    document, chunks = create_document_with_chunks(
        db=db,
        payload=payload,
    )

    return DocumentIngestTextResponse(
        success=True,
        document=document,
        chunks=chunks,
    )


@router.get(
    "/recent",
    response_model=DocumentListResponse,
)
def get_recent_documents(
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    documents = list_recent_documents(
        db=db,
        limit=limit,
    )

    return DocumentListResponse(items=documents)


@router.get(
    "/{document_id}/chunks",
    response_model=DocumentChunkListResponse,
)
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = get_document_by_id(
        db=db,
        document_id=document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="文档不存在",
        )

    chunks = list_document_chunks(
        db=db,
        document_id=document_id,
    )

    return DocumentChunkListResponse(items=chunks)