"""
用户 Pydantic 模型
==================

定义用户相关的数据契约模型。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    """用户基础模型

    包含用户的基本字段。
    """

    username: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    role: str = Field(default="user", max_length=20)
    status: str = Field(default="active", max_length=20)


class UserCreate(UserBase):
    """用户创建模型

    用于用户注册时的数据验证。
    """

    password: Optional[str] = Field(None, min_length=6, max_length=32)


class UserResponse(UserBase):
    """用户响应模型

    用于 API 返回的用户信息，不包含敏感数据。
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    @property
    def phone_masked(self) -> str | None:
        """脱敏后的手机号"""
        if self.phone:
            return self.phone[:3] + "****" + self.phone[-4:]
        return None


class UserInDB(UserResponse):
    """数据库中的用户（含敏感信息）

    用于内部处理，包含密码哈希等敏感信息。
    """

    password_hash: Optional[str] = None
    deleted_at: Optional[datetime] = None
