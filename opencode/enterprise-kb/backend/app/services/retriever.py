"""检索服务：向量检索 + metadata 过滤 + LLM 重排"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.schemas import ChunkResult

logger = logging.getLogger(__name__)


async def _get_query_embedding(query: str) -> list[float]:
    """获取查询文本的 embedding"""
    settings = get_settings()
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.embedding_base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {settings.embedding_api_key}",
                "Content-Type": "application/json",
            },
            json={"model": settings.embedding_model, "input": query},
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]


async def vector_search(
    db: AsyncSession,
    query_embedding: list[float],
    top_k: int,
    file_filter: Optional[str] = None,
    score_threshold: float = 0.3,
) -> list[dict]:
    """pgvector cosine similarity 向量检索"""
    settings = get_settings()
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    sql = """
        SELECT c.id, c.content, c.metadata, c.chunk_index, c.page_num, d.file_name,
               1 - (c.embedding <=> :embedding::vector) AS score
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE 1 - (c.embedding <=> :embedding::vector) > :threshold
    """
    params: dict = {
        "embedding": embedding_str,
        "threshold": score_threshold,
    }

    if file_filter:
        sql += " AND d.file_name = :file_name"
        params["file_name"] = file_filter

    sql += " ORDER BY c.embedding <=> :embedding::vector LIMIT :limit"
    params["limit"] = top_k

    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    return [
        {
            "chunk_id": row.id,
            "content": row.content,
            "metadata": json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata,
            "chunk_index": row.chunk_index,
            "page_num": row.page_num,
            "file_name": row.file_name,
            "score": float(row.score),
        }
        for row in rows
    ]


async def _rerank_with_llm(
    query: str, chunks: list[dict]
) -> list[dict]:
    """用 LLM 对每个 chunk 打相关性分数（0~1），按分数降序排列"""
    if not chunks:
        return []

    settings = get_settings()
    chunk_texts = "\n".join(
        f"[{i+1}] {c['content'][:300]}" for i, c in enumerate(chunks)
    )

    prompt = f"""你是一个相关性评分专家。对以下每个文本片段与查询问题的相关性进行评分（0到1之间，1表示最相关）。

查询问题: {query}

文本片段:
{chunk_texts}

请严格按以下 JSON 数组格式返回评分，不要输出其他内容:
[{{"index": 1, "score": 0.9}}, ...]"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 512,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            # 解析 JSON，去掉可能的 markdown 代码块标记
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            scores = json.loads(content)

            score_map = {item["index"]: item["score"] for item in scores}
            for chunk in chunks:
                idx = chunks.index(chunk) + 1
                chunk["rerank_score"] = score_map.get(idx, 0.0)

            return sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    except Exception as e:
        logger.warning(f"LLM 重排失败，使用原始相似度排序: {e}")
        return chunks


async def retrieve(
    db: AsyncSession,
    query: str,
    file_filter: Optional[str] = None,
    top_k: Optional[int] = None,
) -> list[ChunkResult]:
    """完整检索流程：embedding → 向量检索 → LLM 重排"""
    settings = get_settings()
    k = top_k or settings.retrieval_top_k
    threshold = settings.retrieval_score_threshold

    logger.info(f"检索请求: query='{query[:50]}...', topK={k}, filter={file_filter}")

    # 1. 获取查询 embedding
    query_embedding = await _get_query_embedding(query)

    # 2. 向量检索
    raw_results = await vector_search(
        db, query_embedding, k * 2, file_filter, threshold
    )
    logger.info(f"向量检索返回 {len(raw_results)} 条结果")

    if not raw_results:
        return []

    # 3. LLM 重排
    reranked = await _rerank_with_llm(query, raw_results)

    # 4. 返回 top K
    final = reranked[:k]
    return [
        ChunkResult(
            chunk_id=item["chunk_id"],
            content=item["content"],
            metadata=item["metadata"],
            score=item.get("rerank_score", item["score"]),
            file_name=item["file_name"],
            page_num=item["page_num"],
        )
        for item in final
    ]
