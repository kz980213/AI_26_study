import json
from sqlalchemy.orm import Session

from app.models import DocumentChunk, ChunkEmbedding
from app.services.embedding_service import EmbeddingService


class ChunkEmbeddingService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()

    def embed_chunk(self, chunk_id: int) -> ChunkEmbedding:
        chunk = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.id == chunk_id)
            .first()
        )

        if not chunk:
            raise ValueError(f"chunk 不存在：{chunk_id}")

        if hasattr(chunk, "is_active") and not chunk.is_active:
            raise ValueError("当前 chunk 已被禁用，不能生成 embedding")

        content = getattr(chunk, "content", None) or getattr(chunk, "text", None)

        if not content:
            raise ValueError("chunk 内容为空，不能生成 embedding")

        vector = self.embedding_service.embed_text(content)

        existing = (
            self.db.query(ChunkEmbedding)
            .filter(ChunkEmbedding.chunk_id == chunk_id)
            .first()
        )

        if existing:
            existing.provider = self.embedding_service.provider
            existing.model = self.embedding_service.model
            existing.dimension = self.embedding_service.dimension
            existing.embedding_json = json.dumps(vector, ensure_ascii=False)
            existing.status = "success"
            existing.error_message = None

            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = ChunkEmbedding(
            chunk_id=chunk_id,
            provider=self.embedding_service.provider,
            model=self.embedding_service.model,
            dimension=self.embedding_service.dimension,
            embedding_json=json.dumps(vector, ensure_ascii=False),
            status="success",
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    def get_chunk_embedding(self, chunk_id: int) -> ChunkEmbedding | None:
        return (
            self.db.query(ChunkEmbedding)
            .filter(ChunkEmbedding.chunk_id == chunk_id)
            .first()
        )
    def embed_document_chunks(self, document_id: int, skip_existing: bool = True) -> dict:
        chunks_query = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
        )
    
        if hasattr(DocumentChunk, "is_active"):
            chunks_query = chunks_query.filter(DocumentChunk.is_active == True)
    
        chunks = chunks_query.order_by(DocumentChunk.id.asc()).all()
    
        if not chunks:
            raise ValueError(f"文档不存在，或文档下没有 active chunks：{document_id}")
    
        success_count = 0
        skipped_count = 0
        failed_count = 0
        items = []
    
        for chunk in chunks:
            chunk_id = chunk.id
    
            existing = (
                self.db.query(ChunkEmbedding)
                .filter(ChunkEmbedding.chunk_id == chunk_id)
                .first()
            )
    
            if existing and skip_existing:
                skipped_count += 1
                items.append(
                    {
                        "chunk_id": chunk_id,
                        "status": "skipped",
                        "message": "已存在 embedding，已跳过",
                        "embedding_id": existing.id,
                    }
                )
                continue
            
            try:
                record = self.embed_chunk(chunk_id)
    
                success_count += 1
                items.append(
                    {
                        "chunk_id": chunk_id,
                        "status": "success",
                        "message": "生成成功",
                        "embedding_id": record.id,
                        "dimension": record.dimension,
                    }
                )
    
            except Exception as e:
                failed_count += 1
                items.append(
                    {
                        "chunk_id": chunk_id,
                        "status": "failed",
                        "message": str(e),
                        "embedding_id": None,
                    }
                )
    
        return {
            "document_id": document_id,
            "total_active_chunks": len(chunks),
            "success_count": success_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "items": items,
        }