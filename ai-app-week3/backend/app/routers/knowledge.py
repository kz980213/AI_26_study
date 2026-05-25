from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.document_parser import (
    read_source_file,
    resolve_source_file,
    split_text_into_chunks,
)
from app.services.knowledge_store import (
    init_knowledge_tables,
    list_chunks,
    list_documents,
    save_document_with_chunks,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

init_knowledge_tables()


class IngestRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=200)
    chunk_size: int = Field(500, ge=100, le=2000)
    overlap: int = Field(100, ge=0, le=500)


@router.post("/ingest")
def ingest_document(data: IngestRequest):
    try:
        path = resolve_source_file(data.filename)
        raw_text = read_source_file(path)

        if not raw_text.strip():
            raise ValueError("文档内容为空，无法切分。")

        chunks = split_text_into_chunks(
            raw_text,
            chunk_size=data.chunk_size,
            overlap=data.overlap,
        )

        if not chunks:
            raise ValueError("切分结果为空。")

        document_id = save_document_with_chunks(
            source_name=path.name,
            source_path=str(path),
            file_type=path.suffix.lower().replace(".", ""),
            raw_text=raw_text,
            chunks=chunks,
        )

        return {
            "message": "文档导入并切分成功",
            "document": {
                "id": document_id,
                "source_name": path.name,
                "file_type": path.suffix.lower().replace(".", ""),
                "chunk_count": len(chunks),
            },
            "preview_chunks": chunks[:3],
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/documents")
def get_documents(limit: int = Query(10, ge=1, le=50)):
    return {"items": list_documents(limit=limit)}


@router.get("/chunks")
def get_document_chunks(
    document_id: int = Query(..., ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return {"items": list_chunks(document_id=document_id, limit=limit)}