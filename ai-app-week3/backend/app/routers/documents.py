from sqlalchemy.orm import Session
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from app.services.document_stats_service import get_document_stats

from app.database import get_db
from app.schemas import (
    DocumentChunkListResponse,
    DocumentIngestTextRequest,
    DocumentIngestTextResponse,
    DocumentListResponse,
    DocumentRechunkRequest,
    DocumentRechunkResponse,
    DocumentChunkSearchResponse,
    DocumentChunkUpdateRequest,
    DocumentChunkUpdateResponse,
    DocumentDetailResponse,
    DocumentStatsResponse,
)
from app.services.document_service import (
    create_document_with_chunks,
    get_document_by_id,
    list_document_chunks,
    list_recent_documents,
    rechunk_document,
    search_document_chunks,
    get_document_chunk_by_id,
    update_document_chunk,
)


from app.services.document_file_service import (
    DocumentFileError,
    read_uploaded_text_file,
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
    "/chunks/search",
    response_model=DocumentChunkSearchResponse,
)
def search_chunks(
    keyword: str = Query(..., min_length=1, max_length=100),
    document_id: Optional[int] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    items = search_document_chunks(
        db=db,
        keyword=keyword,
        document_id=document_id,
        limit=limit,
    )

    return DocumentChunkSearchResponse(items=items)

@router.patch(
    "/chunks/{chunk_id}",
    response_model=DocumentChunkUpdateResponse,
)
def update_chunk(
    chunk_id: int,
    payload: DocumentChunkUpdateRequest,
    db: Session = Depends(get_db),
):
    chunk = get_document_chunk_by_id(
        db=db,
        chunk_id=chunk_id,
    )

    if not chunk:
        raise HTTPException(
            status_code=404,
            detail="chunk 不存在",
        )

    updated_chunk = update_document_chunk(
        db=db,
        chunk=chunk,
        content=payload.content,
        is_active=payload.is_active,
        quality_status=payload.quality_status,
        quality_note=payload.quality_note,
    )

    return DocumentChunkUpdateResponse(
        success=True,
        item=updated_chunk,
    )

@router.get(
    "/stats",
    response_model=DocumentStatsResponse,
)
def get_documents_stats(
    db: Session = Depends(get_db),
):
    stats = get_document_stats(db)
    return DocumentStatsResponse(**stats)

@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
)
def get_document_detail(
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

    return DocumentDetailResponse(item=document)

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

@router.post(
    "/{document_id}/rechunk",
    response_model=DocumentRechunkResponse,
)
def rechunk_existing_document(
    document_id: int,
    payload: DocumentRechunkRequest,
    db: Session = Depends(get_db),
):
    if payload.chunk_overlap >= payload.chunk_size:
        raise HTTPException(
            status_code=400,
            detail="chunk_overlap 必须小于 chunk_size",
        )

    document = get_document_by_id(
        db=db,
        document_id=document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="文档不存在",
        )

    updated_document, chunks = rechunk_document(
        db=db,
        document=document,
        payload=payload,
    )

    return DocumentRechunkResponse(
        success=True,
        document=updated_document,
        chunks=chunks,
    )

@router.post(
    "/upload-text",
    response_model=DocumentIngestTextResponse,
)
async def upload_text_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    chunk_size: int = Form(default=500),
    chunk_overlap: int = Form(default=50),
    split_strategy: Literal["chars", "markdown_headings"] = Form(default="chars"),
    db: Session = Depends(get_db),
):
    if chunk_size < 100 or chunk_size > 2000:
        raise HTTPException(
            status_code=422,
            detail="chunk_size 必须在 100 到 2000 之间",
        )

    if chunk_overlap < 0 or chunk_overlap > 500:
        raise HTTPException(
            status_code=422,
            detail="chunk_overlap 必须在 0 到 500 之间",
        )

    if chunk_overlap >= chunk_size:
        raise HTTPException(
            status_code=400,
            detail="chunk_overlap 必须小于 chunk_size",
        )

    try:
        filename, content = await read_uploaded_text_file(file)
    except DocumentFileError as exc:
        raise HTTPException(
            status_code=400,
            detail=exc.message,
        )

    final_title = title.strip() if title and title.strip() else filename

    payload = DocumentIngestTextRequest(
        title=final_title,
        content=content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        split_strategy=split_strategy,
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