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

class LLMCallLog(Base):
    """
    LLM 调用日志表。

    用于记录每一次模型调用的基本信息：
    - 调了哪个模型
    - 属于哪个会话
    - 成功还是失败
    - 花了多久
    - 估算用了多少 token
    """

    __tablename__ = "llm_call_logs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    request_id = Column(String, index=True, nullable=False)
    conversation_id = Column(String, index=True, nullable=True)

    provider = Column(String(50), nullable=False, default="deepseek")
    model = Column(String(100), nullable=False)

    status = Column(String(20), nullable=False, default="success")
    error_code = Column(String(100), nullable=True)
    status_code = Column(Integer, nullable=True)

    prompt_preview = Column(Text, nullable=True)
    response_preview = Column(Text, nullable=True)

    prompt_tokens_est = Column(Integer, nullable=False, default=0)
    completion_tokens_est = Column(Integer, nullable=False, default=0)
    total_tokens_est = Column(Integer, nullable=False, default=0)

    elapsed_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    prompt_template_name = Column(String(100), nullable=True)
    prompt_version = Column(String(100), nullable=True)
    system_prompt_preview = Column(Text, nullable=True)
    
    temperature = Column(String(20), nullable=True)
    max_tokens = Column(Integer, nullable=True)
class StructuredTaskRecord(Base):
    __tablename__ = "structured_tasks"

    id = Column(Integer, primary_key=True, index=True)

    source_text = Column(Text, nullable=False)

    title = Column(String(80), nullable=False)
    category = Column(String(30), nullable=False)
    priority = Column(String(20), nullable=False)

    due_time = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    raw_text = Column(Text, nullable=True)

    retry_count = Column(Integer, nullable=False, default=0)
    elapsed_ms = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class ToolCallLog(Base):
    __tablename__ = "tool_call_logs"

    id = Column(Integer, primary_key=True, index=True)

    source_text = Column(Text, nullable=False)

    tool_name = Column(String(50), nullable=True)

    arguments_json = Column(Text, nullable=True)
    tool_result_json = Column(Text, nullable=True)

    raw_text = Column(Text, nullable=True)

    status = Column(String(20), nullable=False, default="success")
    error_message = Column(Text, nullable=True)

    elapsed_ms = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=False)
    source_type = Column(String(50), nullable=False, default="text")
    content = Column(Text, nullable=False)

    chunk_size = Column(Integer, nullable=False, default=500)
    chunk_overlap = Column(Integer, nullable=False, default=50)
    chunk_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(Integer, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)