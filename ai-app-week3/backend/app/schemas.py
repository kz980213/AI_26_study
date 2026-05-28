from pydantic import BaseModel, Field
from typing import Literal, Optional

class RegisterRequest(BaseModel):
    username: str = Field(...,min_length=3, max_length=50, description="用户名", examples=["kk"])
    password: str = Field(...,min_length=6, max_length=128,description="密码", examples=["123456"])

class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名", examples=["kk"])
    password: str = Field(..., description="密码", examples=["123456"])

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=128, description="旧密码", examples=["123456"])
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码", examples=["123456"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserInfo(BaseModel):
    username: str = Field(..., description="当前登录用户名")

class ChatResponse(BaseModel):
    answer: str

class ChatStreamEvent(BaseModel):
    """
    聊天流式输出事件。

    前后端统一围绕这个结构通信。
    """

    type: Literal["start", "chunk", "done", "error", "heartbeat"]
    message: Optional[str] = None
    content: Optional[str] = None
    index: Optional[int] = None
    conversation_id: Optional[str] = None

    # Day05 新增：用于排查问题
    request_id: Optional[str] = None
    error_code: Optional[str] = None
    status_code: Optional[int] = None
    elapsed_ms: Optional[int] = None

    ##Week5 Day01 新增：模型调用信息
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt_tokens_est: Optional[int] = None
    completion_tokens_est: Optional[int] = None
    total_tokens_est: Optional[int] = None

    # Week5 Day03：上下文信息
    context_messages_count: Optional[int] = None
    context_tokens_est: Optional[int] = None
    truncated_messages_count: Optional[int] = None

    # Week5 Day04：Prompt 版本信息
    prompt_template_name: Optional[str] = None
    prompt_version: Optional[str] = None
    system_prompt_preview: Optional[str] = None

class SaveChatMessageRequest(BaseModel):
    """
    手动保存聊天消息。

    用于：
    - 停止输出时保存部分 assistant 回复
    - 后续也可以用于补录消息
    """

    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    request_id: Optional[str] = None