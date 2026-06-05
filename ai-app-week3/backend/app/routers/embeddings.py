import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.chunk_embedding_service import ChunkEmbeddingService

from pydantic import BaseModel, Field

from app.services.embedding_search_service import EmbeddingSearchService

from typing import Optional

router = APIRouter(prefix="/ai/embeddings", tags=["embeddings"])


@router.post("/chunks/{chunk_id}")
def embed_chunk(chunk_id: int, db: Session = Depends(get_db)):
    service = ChunkEmbeddingService(db)

    try:
        record = service.embed_chunk(chunk_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": record.id,
        "chunk_id": record.chunk_id,
        "provider": record.provider,
        "model": record.model,
        "dimension": record.dimension,
        "embedding": json.loads(record.embedding_json),
        "status": record.status,
        "error_message": record.error_message,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


@router.get("/chunks/{chunk_id}")
def get_chunk_embedding(chunk_id: int, db: Session = Depends(get_db)):
    service = ChunkEmbeddingService(db)

    record = service.get_chunk_embedding(chunk_id)

    if not record:
        raise HTTPException(status_code=404, detail="当前 chunk 还没有 embedding")

    return {
        "id": record.id,
        "chunk_id": record.chunk_id,
        "provider": record.provider,
        "model": record.model,
        "dimension": record.dimension,
        "embedding": json.loads(record.embedding_json),
        "status": record.status,
        "error_message": record.error_message,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }

@router.post("/documents/{document_id}/chunks")
def embed_document_chunks(
    document_id: int,
    skip_existing: bool = True,
    db: Session = Depends(get_db),
):
    service = ChunkEmbeddingService(db)

    try:
        result = service.embed_document_chunks(
            document_id=document_id,
            skip_existing=skip_existing,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


from app.schemas import EmbeddingSearchRequest, EmbeddingSearchResponse
from app.services.embedding_search_service import search_similar_chunks

router = APIRouter(prefix="/ai/embeddings", tags=["embeddings"])


@router.post("/search", response_model=EmbeddingSearchResponse)
def search_embeddings(
    payload: EmbeddingSearchRequest,
    db: Session = Depends(get_db),
):
    return search_similar_chunks(
        db=db,
        query=payload.query,
        document_id=payload.document_id,
        top_k=payload.top_k,
    )

class EmbeddingSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="用户检索问题")
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: Optional[int] = None
    only_active: bool = True
    quality_status: Optional[str] = Field(
        default=None,
        description="可选：unknown / good / needs_review / bad",
    )
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="最低相似度分数过滤，例如 0.3",
    )

@router.post("/search")
def search_embeddings(
    payload: EmbeddingSearchRequest,
    db: Session = Depends(get_db),
):
    try:
        result = search_similar_chunks(
            db=db,
            query=payload.query,
            top_k=payload.top_k,
            document_id=payload.document_id,
            only_active=payload.only_active,
            quality_status=payload.quality_status,
            score_threshold=payload.score_threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result