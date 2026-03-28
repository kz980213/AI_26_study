from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Auth ---
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class UserLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: UUID
    username: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Ingest ---
class UploadResponse(BaseModel):
    document_id: UUID
    file_name: str
    chunk_count: int
    message: str


# --- Chat ---
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[UUID] = None
    file_filter: Optional[str] = Field(None, description="按文件名过滤")


class CitationItem(BaseModel):
    chunk_id: UUID
    content: str
    metadata: dict
    score: float


class ChatTokenEvent(BaseModel):
    type: str = "token"
    content: str


class ChatDoneEvent(BaseModel):
    type: str = "done"
    citations: list[CitationItem] = []


class ChatErrorEvent(BaseModel):
    type: str = "error"
    message: str


# --- Session ---
class SessionCreate(BaseModel):
    title: str = "新对话"


class SessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    citations: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Eval ---
class EvalResponse(BaseModel):
    message: str
    result_file: str


# --- Retriever ---
class ChunkResult(BaseModel):
    chunk_id: UUID
    content: str
    metadata: dict
    score: float
    file_name: str
    page_num: Optional[int] = None
