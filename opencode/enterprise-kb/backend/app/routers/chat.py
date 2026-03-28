"""对话路由：SSE 流式问答"""
from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.schemas import ChunkResult
from app.services.generator import stream_generate
from app.services.retriever import retrieve
from app.services.session import (
    add_message,
    create_session,
    get_history,
    get_session,
)

router = APIRouter(prefix="/chat", tags=["对话"])
logger = logging.getLogger(__name__)


async def _get_current_user_id(token: str = Query(...)) -> uuid.UUID:
    """从 query param 的 token 中解析用户 ID（SSE 不支持 Header）"""
    user_id_str = decode_access_token(token)
    if not user_id_str:
        raise HTTPException(status_code=401, detail="无效的认证 token")
    try:
        return uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的用户 ID")


@router.get("/stream")
async def chat_stream(
    question: str = Query(..., min_length=1, max_length=2000),
    token: str = Query(..., description="JWT access token"),
    session_id: str | None = Query(None, description="会话 ID"),
    file_filter: str | None = Query(None, description="按文件名过滤"),
    db: AsyncSession = Depends(get_db),
):
    """SSE 流式问答接口"""
    user_id = await _get_current_user_id(token)

    # 获取或创建会话
    sess = None
    history: list[dict] = []
    if session_id:
        sess = await get_session(db, uuid.UUID(session_id), user_id)
        if not sess:
            raise HTTPException(status_code=404, detail="会话不存在或无权访问")
        history = await get_history(db, sess.id)
    else:
        sess = await create_session(db, user_id, title=question[:50])

    # 保存用户消息
    await add_message(db, sess.id, "user", question)
    await db.commit()

    # 检索相关 chunks
    try:
        chunks: list[ChunkResult] = await retrieve(
            db, question, file_filter=file_filter
        )
    except Exception as e:
        logger.error(f"检索失败: {e}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")

    if not chunks:
        raise HTTPException(status_code=404, detail="未找到相关文档，请先上传知识库文档")

    async def event_generator():
        full_answer = ""
        citations = []
        try:
            async for event in stream_generate(question, chunks, history):
                if event["type"] == "token":
                    full_answer += event["content"]
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                elif event["type"] == "done":
                    citations = event.get("citations", [])
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                elif event["type"] == "error":
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    return
        except Exception as e:
            logger.error(f"流式生成异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
            return

        # 保存助手消息
        try:
            from app.core.database import async_session_factory
            async with async_session_factory() as inner_db:
                await add_message(inner_db, sess.id, "assistant", full_answer, citations)
                await inner_db.commit()
        except Exception as e:
            logger.error(f"保存消息失败: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
