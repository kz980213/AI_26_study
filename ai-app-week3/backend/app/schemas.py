from pydantic import BaseModel, Field

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