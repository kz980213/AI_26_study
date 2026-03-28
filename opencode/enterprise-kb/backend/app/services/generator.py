"""生成服务：Prompt 构造 + 流式生成 + 引用解析"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import AsyncGenerator
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.models.schemas import ChunkResult, CitationItem

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的知识库问答助手。请根据提供的参考文档片段回答用户问题。

规则：
1. 仅基于参考文档中的信息作答，如果参考文档中没有相关信息，请明确说明
2. 在回答中使用 [数字] 标注引用来源，数字对应参考文档的编号
3. 每个关键论点至少引用一个来源
4. 用简洁专业的中文回答
5. 不要编造参考文档中没有的信息"""

USER_PROMPT_TEMPLATE = """参考文档：
{chunks_text}

用户问题：{question}

请基于以上参考文档回答问题，并用 [数字] 标注引用来源。"""


def _format_chunks(chunks: list[ChunkResult]) -> str:
    """将 chunk 列表格式化为 prompt 中的文本"""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        source_info = f"（来源: {chunk.file_name}"
        if chunk.page_num:
            source_info += f", 第{chunk.page_num}页"
        source_info += "）"
        parts.append(f"[{i}] {chunk.content}{source_info}")
    return "\n\n".join(parts)


def _parse_citations(
    answer: str, chunks: list[ChunkResult]
) -> list[CitationItem]:
    """从 LLM 输出中解析 [数字] 引用，映射回对应 chunk"""
    citations_map: dict[int, CitationItem] = {}
    pattern = re.compile(r"\[(\d+)\]")
    for match in pattern.finditer(answer):
        idx = int(match.group(1))
        if 1 <= idx <= len(chunks) and idx not in citations_map:
            chunk = chunks[idx - 1]
            citations_map[idx] = CitationItem(
                chunk_id=chunk.chunk_id,
                content=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                metadata=chunk.metadata,
                score=chunk.score,
            )
    return list(citations_map.values())


async def stream_generate(
    question: str,
    chunks: list[ChunkResult],
    history: list[dict] | None = None,
) -> AsyncGenerator[dict, None]:
    """
    流式生成答案，yield SSE 事件字典。
    事件格式：
    - {"type": "token", "content": "..."}
    - {"type": "done", "citations": [...]}
    """
    settings = get_settings()
    start_time = time.time()
    prompt_tokens = 0
    completion_tokens = 0

    chunks_text = _format_chunks(chunks)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        chunks_text=chunks_text, question=question
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # 加入对话历史（最近 5 轮）
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_prompt})

    full_answer = ""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{settings.llm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 2048,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        token_content = delta.get("content", "")
                        if token_content:
                            full_answer += token_content
                            yield {"type": "token", "content": token_content}
                            completion_tokens += 1

                        # 提取 usage（最后一个 chunk 可能包含）
                        if "usage" in data:
                            prompt_tokens = data["usage"].get("prompt_tokens", prompt_tokens)
                            completion_tokens = data["usage"].get("completion_tokens", completion_tokens)
                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        logger.error(f"LLM 流式生成失败: {e}")
        yield {"type": "error", "message": f"生成失败: {str(e)}"}
        return

    # 解析引用
    citations = _parse_citations(full_answer, chunks)

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(
        f"生成完成: 耗时={elapsed_ms}ms, "
        f"prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}, "
        f"引用数={len(citations)}, "
        f"预估费用={(prompt_tokens + completion_tokens) * settings.token_price_per_1k / 1000:.4f}元"
    )

    yield {
        "type": "done",
        "citations": [c.model_dump() for c in citations],
    }


def generate_sync(
    question: str,
    chunks: list[ChunkResult],
    history: list[dict] | None = None,
) -> str:
    """非流式生成，用于评测脚本"""
    settings = get_settings()
    chunks_text = _format_chunks(chunks)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        chunks_text=chunks_text, question=question
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_prompt})

    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def _call() -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 2048,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    return loop.run_until_complete(_call())
