"""对话会话管理服务"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import ChatMessage, ChatSession

logger = logging.getLogger(__name__)


async def create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str = "新对话",
) -> ChatSession:
    """创建新对话会话"""
    session = ChatSession(
        user_id=user_id,
        title=title,
    )
    db.add(session)
    await db.flush()
    logger.info(f"创建会话: {session.id}, 用户: {user_id}")
    return session


async def get_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[ChatSession]:
    """获取会话，校验归属用户"""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> list[ChatSession]:
    """列出用户的对话会话"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def add_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    role: str,
    content: str,
    citations: Optional[list[dict]] = None,
) -> ChatMessage:
    """添加对话消息"""
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        citations=json.dumps(citations, ensure_ascii=False) if citations else None,
    )
    db.add(msg)

    # 更新会话时间
    session = await db.get(ChatSession, session_id)
    if session:
        session.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return msg


async def get_history(
    db: AsyncSession,
    session_id: uuid.UUID,
    limit: int = 20,
) -> list[dict]:
    """获取对话历史，返回 OpenAI 格式的 messages"""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


async def delete_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """删除会话及其消息"""
    session = await get_session(db, session_id, user_id)
    if not session:
        return False
    await db.delete(session)
    await db.flush()
    return True
