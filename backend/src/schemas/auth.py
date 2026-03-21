"""
认证 Pydantic 模型
=================

定义认证相关的数据契约模型。
"""

from pydantic import BaseModel, Field


class UsernameRegisterRequest(BaseModel):
    """用户名注册请求"""

    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    password: str = Field(..., min_length=6, max_length=32)


class UsernameLoginRequest(BaseModel):
    """用户名登录请求"""

    username: str
    password: str


class PhoneRegisterRequest(BaseModel):
    """手机号注册请求"""

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=6, max_length=6)
    password: str | None = Field(None, min_length=6, max_length=32)
    username: str | None = Field(None, min_length=3, max_length=20)


class PhoneLoginRequest(BaseModel):
    """手机号登录请求"""

    phone: str
    code: str = Field(..., min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""

    phone: str
    code: str
    new_password: str = Field(..., min_length=6, max_length=32)


class BindPhoneRequest(BaseModel):
    """绑定手机请求"""

    phone: str
    code: str


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""

    old_password: str
    new_password: str = Field(..., min_length=6, max_length=32)


class TokenResponse(BaseModel):
    """Token 响应"""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
