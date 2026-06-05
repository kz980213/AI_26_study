import hashlib
import json
import math
import re
from typing import List, Optional, Any, Dict

from sqlalchemy.orm import Session

from app.models import DocumentChunk, ChunkEmbedding

from app.services.embedding_service import EmbeddingService

# from app.services.embedding_service import create_mock_embedding
# from app.services.embedding_service import parse_vector
# from app.services.embedding_service import cosine_similarity
# from app.services.document_chunk_service import get_chunk_content


def create_mock_embedding(text: str, dim: int = 32) -> List[float]:
    """
    教学版 mock embedding。

    注意：
    真实项目中这里会换成真实 embedding 模型 API。
    现在先用可重复的 hashing 方法，让相似文本尽量得到相近向量。
    """
    text = (text or "").strip().lower()
    vector = [0.0 for _ in range(dim)]

    tokens = re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]", text)

    for token in tokens:
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % dim
        sign = 1 if int(digest[8:10], 16) % 2 == 0 else -1
        vector[index] += sign * 1.0

    norm = math.sqrt(sum(x * x for x in vector))

    if norm == 0:
        return vector

    return [round(x / norm, 6) for x in vector]


def parse_vector(embedding_json) -> List[float]:
    """
    兼容两种情况：
    1. 数据库里存的是 JSON 字符串
    2. 已经被 ORM 解析成 list
    """
    if isinstance(embedding_json, list):
        return [float(x) for x in embedding_json]

    if not embedding_json:
        return []

    return [float(x) for x in json.loads(embedding_json)]


def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """
    余弦相似度：
    越接近 1，越相似；
    越接近 0，越不相关；
    小于 0，方向相反。
    """
    if not vector_a or not vector_b:
        return 0.0

    if len(vector_a) != len(vector_b):
        return 0.0

    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return round(dot / (norm_a * norm_b), 6)


def get_chunk_content(chunk: DocumentChunk) -> str:
    """
    兼容不同字段名。
    如果你当前模型里字段名确定是 content，可以只保留 chunk.content。
    """
    return (
        getattr(chunk, "content", None)
        or getattr(chunk, "text", None)
        or getattr(chunk, "chunk_text", None)
        or ""
    )


def search_similar_chunks(
    db: Session,
    query: str,
    top_k: int = 5,
    document_id: Optional[int] = None,
    only_active: bool = True,
    quality_status: Optional[str] = None,
    score_threshold: Optional[float] = None,
) -> Dict[str, Any]:
    if not query or not query.strip():
        raise ValueError("query 不能为空")

    if top_k <= 0:
        raise ValueError("top_k 必须大于 0")

    top_k = min(top_k, 20)

    query_vector = create_mock_embedding(query)

    db_query = (
        db.query(ChunkEmbedding, DocumentChunk)
        .join(DocumentChunk, ChunkEmbedding.chunk_id == DocumentChunk.id)
    )

    applied_filters = {
        "document_id": document_id,
        "only_active": only_active,
        "quality_status": quality_status,
        "score_threshold": score_threshold,
    }

    if document_id is not None:
        db_query = db_query.filter(DocumentChunk.document_id == document_id)

    if only_active:
        if hasattr(DocumentChunk, "is_active"):
            db_query = db_query.filter(DocumentChunk.is_active == True)

        if hasattr(DocumentChunk, "status"):
            db_query = db_query.filter(DocumentChunk.status == "active")

    if quality_status:
        if hasattr(DocumentChunk, "quality_status"):
            db_query = db_query.filter(DocumentChunk.quality_status == quality_status)

    rows = db_query.all()

    scored_results = []

    for embedding_record, chunk in rows:
        try:
            chunk_vector = parse_vector(embedding_record.embedding_json)
            score = cosine_similarity(query_vector, chunk_vector)

            if score_threshold is not None and score < score_threshold:
                continue

            content = get_chunk_content(chunk)

            scored_results.append(
                {
                    "chunk_id": chunk.id,
                    "document_id": getattr(chunk, "document_id", None),
                    "embedding_id": embedding_record.id,
                    "score": round(score, 6),
                    "content": content,
                    "content_preview": content[:180],
                    "provider": embedding_record.provider,
                    "model": embedding_record.model,
                    "dimension": embedding_record.dimension,
                    "is_active": getattr(chunk, "is_active", None),
                    "status": getattr(chunk, "status", None),
                    "quality_status": getattr(chunk, "quality_status", None),
                    "quality_note": getattr(chunk, "quality_note", None),
                }
            )
        except Exception as e:
            scored_results.append(
                {
                    "chunk_id": chunk.id,
                    "document_id": getattr(chunk, "document_id", None),
                    "embedding_id": embedding_record.id,
                    "score": -1,
                    "content": "",
                    "content_preview": "",
                    "provider": embedding_record.provider,
                    "model": embedding_record.model,
                    "dimension": embedding_record.dimension,
                    "is_active": getattr(chunk, "is_active", None),
                    "status": getattr(chunk, "status", None),
                    "quality_status": getattr(chunk, "quality_status", None),
                    "quality_note": getattr(chunk, "quality_note", None),
                    "error_message": str(e),
                }
            )

    scored_results.sort(key=lambda item: item["score"], reverse=True)

    top_results = scored_results[:top_k]

    scores = [item["score"] for item in scored_results if item["score"] >= 0]

    return {
        "query": query,
        "top_k": top_k,
        "document_id": document_id,
        "only_active": only_active,
        "quality_status": quality_status,
        "score_threshold": score_threshold,
        "applied_filters": applied_filters,
        "total_candidates": len(rows),
        "returned_count": len(top_results),
        "matched_after_score_filter": len(scored_results),
        "max_score": max(scores) if scores else None,
        "min_score": min(scores) if scores else None,
        "results": top_results,
    }



class EmbeddingSearchService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: int | None = None,
        only_active: bool = True,
    ) -> dict[str, Any]:
        if not query or not query.strip():
            raise ValueError("query 不能为空")

        if top_k <= 0:
            raise ValueError("top_k 必须大于 0")

        top_k = min(top_k, 20)

        query_embedding = self.embedding_service.embed_text(query)

        records_query = (
            self.db.query(ChunkEmbedding, DocumentChunk)
            .join(DocumentChunk, ChunkEmbedding.chunk_id == DocumentChunk.id)
        )

        if document_id is not None:
            records_query = records_query.filter(
                DocumentChunk.document_id == document_id
            )

        if only_active and hasattr(DocumentChunk, "is_active"):
            records_query = records_query.filter(DocumentChunk.is_active == True)

        records = records_query.all()

        results = []

        for embedding_record, chunk in records:
            try:
                chunk_embedding = json.loads(embedding_record.embedding_json)
                score = self._cosine_similarity(query_embedding, chunk_embedding)

                results.append(
                    {
                        "chunk_id": chunk.id,
                        "document_id": getattr(chunk, "document_id", None),
                        "embedding_id": embedding_record.id,
                        "score": round(score, 6),
                        "content": self._get_chunk_content(chunk),
                        "content_preview": self._get_chunk_content(chunk)[:160],
                        "provider": embedding_record.provider,
                        "model": embedding_record.model,
                        "dimension": embedding_record.dimension,
                        "quality_status": getattr(chunk, "quality_status", None),
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "chunk_id": chunk.id,
                        "document_id": getattr(chunk, "document_id", None),
                        "embedding_id": embedding_record.id,
                        "score": -1,
                        "content": "",
                        "content_preview": "",
                        "provider": embedding_record.provider,
                        "model": embedding_record.model,
                        "dimension": embedding_record.dimension,
                        "quality_status": getattr(chunk, "quality_status", None),
                        "error_message": str(e),
                    }
                )

        results = sorted(results, key=lambda item: item["score"], reverse=True)
        top_results = results[:top_k]

        return {
            "query": query,
            "top_k": top_k,
            "document_id": document_id,
            "only_active": only_active,
            "total_candidates": len(records),
            "results": top_results,
        }

    def _cosine_similarity(self, vector_a: list[float], vector_b: list[float]) -> float:
        if not vector_a or not vector_b:
            return 0.0

        length = min(len(vector_a), len(vector_b))

        a = vector_a[:length]
        b = vector_b[:length]

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _get_chunk_content(self, chunk: DocumentChunk) -> str:
        for field_name in ["content", "text", "chunk_text"]:
            value = getattr(chunk, field_name, None)
            if value:
                return value

        return ""