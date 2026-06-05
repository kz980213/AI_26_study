from typing import Any

from sqlalchemy.orm import Session

from app.models import ChunkEmbedding
from app.services.chunk_embedding_service import ChunkEmbeddingService
from app.services.embedding_stats_service import get_embedding_stats


def delete_chunk_embedding(db: Session, chunk_id: int) -> dict[str, Any]:
    record = (
        db.query(ChunkEmbedding)
        .filter(ChunkEmbedding.chunk_id == chunk_id)
        .first()
    )

    if not record:
        return {
            "chunk_id": chunk_id,
            "deleted": False,
            "embedding_id": None,
            "message": "当前 chunk 没有 embedding，无需删除",
        }

    embedding_id = record.id

    db.delete(record)
    db.commit()

    return {
        "chunk_id": chunk_id,
        "deleted": True,
        "embedding_id": embedding_id,
        "message": "embedding 删除成功",
    }


def rebuild_chunk_embedding(db: Session, chunk_id: int) -> dict[str, Any]:
    delete_result = delete_chunk_embedding(db, chunk_id)

    service = ChunkEmbeddingService(db)
    record = service.embed_chunk(chunk_id)

    return {
        "chunk_id": chunk_id,
        "deleted_before_rebuild": delete_result["deleted"],
        "embedding_id": record.id,
        "provider": record.provider,
        "model": record.model,
        "dimension": record.dimension,
        "status": record.status,
        "message": "chunk embedding 重建成功",
    }


def rebuild_document_embeddings(
    db: Session,
    document_id: int,
) -> dict[str, Any]:
    service = ChunkEmbeddingService(db)

    result = service.embed_document_chunks(
        document_id=document_id,
        skip_existing=False,
    )

    result["message"] = "文档 embeddings 重建完成"
    result["mode"] = "force_rebuild"

    return result


def get_rag_readiness(db: Session) -> dict[str, Any]:
    stats = get_embedding_stats(db)

    checks = []

    has_documents = stats["total_documents"] > 0
    has_active_chunks = stats["active_chunks"] > 0
    has_embedding_records = stats["embedding_records"] > 0
    full_embedding_coverage = stats["missing_active_chunks"] == 0
    can_search = stats["embedded_active_chunks"] > 0

    checks.append(
        {
            "key": "has_documents",
            "label": "是否已有文档",
            "passed": has_documents,
            "message": "已有文档" if has_documents else "还没有导入文档",
        }
    )

    checks.append(
        {
            "key": "has_active_chunks",
            "label": "是否存在 active chunks",
            "passed": has_active_chunks,
            "message": "存在可用 chunks" if has_active_chunks else "没有可用 chunks",
        }
    )

    checks.append(
        {
            "key": "has_embedding_records",
            "label": "是否已有 embedding 记录",
            "passed": has_embedding_records,
            "message": "已有 embedding 记录"
            if has_embedding_records
            else "还没有生成 embedding",
        }
    )

    checks.append(
        {
            "key": "full_embedding_coverage",
            "label": "active chunks 是否全部向量化",
            "passed": full_embedding_coverage,
            "message": "active chunks 已全部向量化"
            if full_embedding_coverage
            else f"还有 {stats['missing_active_chunks']} 个 active chunks 缺失 embedding",
        }
    )

    checks.append(
        {
            "key": "can_search",
            "label": "是否可以进行向量检索",
            "passed": can_search,
            "message": "可以进行向量检索"
            if can_search
            else "当前没有可检索的 embedding",
        }
    )

    ready_for_rag = all(item["passed"] for item in checks)

    suggestions = []

    if not has_documents:
        suggestions.append("先使用 Week7 的文档导入功能导入文本或 Markdown 文件")

    if has_documents and not has_active_chunks:
        suggestions.append("检查 document_chunks 是否都被禁用，至少保留一些 active chunks")

    if has_active_chunks and not full_embedding_coverage:
        suggestions.append("使用 Day02 批量 embedding 或 Day07 文档重建功能补齐缺失向量")

    if not has_embedding_records:
        suggestions.append("先执行单个 chunk embedding 或文档级批量 embedding")

    if ready_for_rag:
        suggestions.append("可以进入 Week9：RAG 问答闭环")

    return {
        "ready_for_rag": ready_for_rag,
        "checks": checks,
        "suggestions": suggestions,
        "stats": stats,
    }