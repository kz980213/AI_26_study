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

    这是后端推给前端的统一事件结构。
    后面接真实大模型时，也尽量继续保持这个结构。
    """

    type: Literal["start", "chunk", "done", "error", "heartbeat"]
    message: Optional[str] = None
    content: Optional[str] = None
    index: Optional[int] = None
    conversation_id: Optional[str] = None