from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Text
from app.database import Base

import uuid
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class ChatConversation(Base):
    """
    聊天会话表。

    一个 conversation 对应一轮持续聊天。
    """

    __tablename__ = "chat_conversations"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False, default="新会话")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class ChatMessage(Base):
    """
    聊天消息表。

    role:
    - user：用户消息
    - assistant：AI 回复
    """

    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String,
        ForeignKey("chat_conversations.id"),
        index=True,
        nullable=False,
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    request_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)