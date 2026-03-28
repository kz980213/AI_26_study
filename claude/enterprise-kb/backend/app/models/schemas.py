"""
Pydantic request/response schemas
定义 API 输入输出数据结构
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field
import uuid


# ─────────────── 认证相关 ───────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒


class UserInfo(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────── 文档 / 入库相关 ───────────────

class UploadResponse(BaseModel):
    document_id: uuid.UUID
    file_name: str
    chunk_count: int
    message: str


class DocumentInfo(BaseModel):
    id: uuid.UUID
    file_name: str
    file_type: Optional[str]
    file_size: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────── 检索 / 问答相关 ───────────────

class ChunkResult(BaseModel):
    """单个检索结果块"""
    chunk_id: str
    content: str
    metadata: dict
    score: float  # 相关性分数（0~1）


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    top_k: Optional[int] = Field(None, ge=1, le=20)
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    file_name_filter: Optional[str] = None  # 按文件名过滤


class CitationItem(BaseModel):
    """引用条目，对应 LLM 输出中的 [数字] 标注"""
    index: int       # 编号，对应 [1][2]...
    chunk_id: str
    content: str
    metadata: dict
    score: float


class SSETokenEvent(BaseModel):
    """SSE 流式 token 事件"""
    type: str = "token"
    content: str


class SSEDoneEvent(BaseModel):
    """SSE 结束事件，附带引用列表"""
    type: str = "done"
    citations: List[CitationItem]
    session_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0  # 预估费用（元）


class SSEErrorEvent(BaseModel):
    """SSE 错误事件"""
    type: str = "error"
    message: str


# ─────────────── 会话历史相关 ───────────────

class MessageSchema(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: List[Any]
    created_at: datetime

    class Config:
        from_attributes = True


class SessionSchema(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    created_at: datetime
    messages: List[MessageSchema] = []

    class Config:
        from_attributes = True


# ─────────────── 评测相关 ───────────────

class EvalRunRequest(BaseModel):
    golden_set_path: Optional[str] = None  # 不传则使用默认路径


class EvalResult(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    sample_count: int
    output_file: str
