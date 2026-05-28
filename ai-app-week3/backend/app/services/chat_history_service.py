import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy.orm import Session

from app.models import ChatConversation, ChatMessage


ChatRole = Literal["user", "assistant"]


def create_conversation_if_not_exists(
    db: Session,
    conversation_id: str | None = None,
    title: str | None = None,
) -> ChatConversation:
    """
    如果 conversation_id 存在，则复用会话。
    如果不存在，则创建新会话。
    """

    if conversation_id:
        conversation = (
            db.query(ChatConversation)
            .filter(ChatConversation.id == conversation_id)
            .first()
        )

        if conversation:
            return conversation

    conversation = ChatConversation(
        id=conversation_id or str(uuid.uuid4()),
        title=title or "新会话",
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def update_conversation_time(db: Session, conversation_id: str) -> None:
    conversation = (
        db.query(ChatConversation)
        .filter(ChatConversation.id == conversation_id)
        .first()
    )

    if not conversation:
        return

    conversation.updated_at = datetime.utcnow()
    db.commit()


def save_chat_message(
    db: Session,
    conversation_id: str,
    role: ChatRole,
    content: str,
    request_id: str | None = None,
) -> ChatMessage:
    """
    保存一条聊天消息。
    """

    message = ChatMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        request_id=request_id,
    )

    db.add(message)
    update_conversation_time(db, conversation_id)
    db.commit()
    db.refresh(message)

    return message


def get_recent_chat_messages(
    db: Session,
    conversation_id: str,
    limit: int = 8,
) -> list[dict[str, str]]:
    """
    获取最近几条消息，用于后续多轮上下文。

    返回格式直接接近 OpenAI / DeepSeek messages 格式：
    [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
    """

    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    rows.reverse()

    return [
        {
            "role": row.role,
            "content": row.content,
        }
        for row in rows
        if row.role in ["user", "assistant"]
    ]


def get_conversation_messages(
    db: Session,
    conversation_id: str,
    limit: int = 100,
) -> list[ChatMessage]:
    """
    获取一个会话的全部消息。
    """

    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    rows.reverse()

    return rows


def list_recent_conversations(
    db: Session,
    limit: int = 20,
) -> list[ChatConversation]:
    """
    获取最近会话列表，今天先预留给后续使用。
    """

    return (
        db.query(ChatConversation)
        .order_by(ChatConversation.updated_at.desc())
        .limit(limit)
        .all()
    )