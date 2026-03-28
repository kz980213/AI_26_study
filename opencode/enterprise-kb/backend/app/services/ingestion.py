"""文档入库服务：文档解析 → chunking → embedding → 入库"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.db import Chunk, Document

logger = logging.getLogger(__name__)


async def _call_embedding_with_retry(texts: list[str]) -> list[list[float]]:
    """调用 embedding API，失败自动重试 3 次，exponential backoff"""
    settings = get_settings()
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{settings.embedding_base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {settings.embedding_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.embedding_model,
                        "input": texts,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                # 排序确保顺序一致
                sorted_data = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_data]
        except Exception as e:
            wait = 2 ** (attempt - 1)
            logger.warning(f"Embedding 调用失败（第 {attempt} 次），{wait}s 后重试: {e}")
            if attempt < max_retries:
                await asyncio.sleep(wait)
            else:
                raise RuntimeError(f"Embedding 调用连续失败 {max_retries} 次: {e}")


def _parse_pdf(file_bytes: bytes) -> list[dict]:
    """解析 PDF，返回 [{content: str, page_num: int}]"""
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(file_bytes))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append({"content": text.strip(), "page_num": i + 1})
    return pages


def _parse_markdown(file_bytes: bytes) -> list[dict]:
    """解析 Markdown，返回 [{content: str, page_num: int}]"""
    import markdown

    text = file_bytes.decode("utf-8", errors="ignore").strip()
    if not text:
        return []
    return [{"content": text, "page_num": 1}]


def _split_paragraphs(text: str) -> list[str]:
    """按段落切分文本"""
    paragraphs = text.split("\n\n")
    return [p.strip() for p in paragraphs if p.strip()]


def _chunk_text(
    paragraphs: list[str], chunk_size: int, overlap: int
) -> list[str]:
    """将段落合并为指定大小的 chunk，保留 overlap"""
    if not paragraphs:
        return []
    chunks: list[str] = []
    current = ""
    current_paragraphs: list[str] = []

    for para in paragraphs:
        if not current:
            current = para
            current_paragraphs = [para]
        elif len(current) + len(para) + 2 <= chunk_size:
            current = current + "\n\n" + para
            current_paragraphs.append(para)
        else:
            chunks.append(current)
            # 保留 overlap 个段落
            overlap_text = "\n\n".join(current_paragraphs[-overlap:]) if overlap > 0 else ""
            current = overlap_text + "\n\n" + para if overlap_text else para
            current_paragraphs = current_paragraphs[-overlap:] + [para] if overlap > 0 else [para]

    if current.strip():
        chunks.append(current)
    return chunks


async def ingest_document(
    file_bytes: bytes,
    file_name: str,
    file_type: str,
    db: AsyncSession,
    uploaded_by: Optional[uuid.UUID] = None,
) -> Document:
    """完整入库流程：解析 → 切分 → embedding → 存储"""
    settings = get_settings()
    logger.info(f"开始入库文档: {file_name}, 类型: {file_type}")

    # 1. 解析文档
    if file_type.lower() == "pdf":
        pages = _parse_pdf(file_bytes)
    elif file_type.lower() in ("md", "markdown"):
        pages = _parse_markdown(file_bytes)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

    if not pages:
        raise ValueError("文档内容为空，无法入库")

    # 2. 创建 Document 记录
    doc = Document(
        file_name=file_name,
        file_type=file_type.lower(),
        uploaded_by=uploaded_by,
        chunk_count=0,
    )
    db.add(doc)
    await db.flush()

    # 3. 切分所有 chunk
    all_chunks: list[dict] = []
    chunk_index = 0
    for page in pages:
        paragraphs = _split_paragraphs(page["content"])
        text_chunks = _chunk_text(
            paragraphs, settings.chunk_size, settings.chunk_overlap
        )
        for tc in text_chunks:
            all_chunks.append({
                "content": tc,
                "page_num": page["page_num"],
                "chunk_index": chunk_index,
            })
            chunk_index += 1

    if not all_chunks:
        raise ValueError("切分后无有效 chunk")

    # 4. 批量 embedding（每批 20 条）
    batch_size = 20
    all_embeddings: list[list[float]] = []
    for i in range(0, len(all_chunks), batch_size):
        batch = [c["content"] for c in all_chunks[i : i + batch_size]]
        embeddings = await _call_embedding_with_retry(batch)
        all_embeddings.extend(embeddings)
        logger.info(f"Embedding 进度: {min(i + batch_size, len(all_chunks))}/{len(all_chunks)}")

    # 5. 存储 chunk
    now = datetime.now(timezone.utc).isoformat()
    for chunk_data, emb in zip(all_chunks, all_embeddings):
        chunk_obj = Chunk(
            document_id=doc.id,
            content=chunk_data["content"],
            embedding=emb,
            chunk_index=chunk_data["chunk_index"],
            page_num=chunk_data["page_num"],
            metadata_=json.dumps({
                "file_name": file_name,
                "page_num": chunk_data["page_num"],
                "chunk_index": chunk_data["chunk_index"],
                "created_at": now,
            }, ensure_ascii=False),
        )
        db.add(chunk_obj)

    doc.chunk_count = len(all_chunks)
    await db.flush()
    logger.info(f"文档入库完成: {file_name}, 共 {len(all_chunks)} 个 chunk")
    return doc
