"""
短信 Pydantic 模型
==================

定义短信验证码相关的数据契约模型。
"""

from enum import Enum

from pydantic import BaseModel, Field


class SmsScene(str, Enum):
    """验证码场景枚举

    定义系统中所有支持的验证码使用场景。
    """

    REGISTER = "register"
    LOGIN = "login"
    BIND = "bind"
    UNBIND = "unbind"
    RESET_PASSWORD = "reset_password"


class SmsSendRequest(BaseModel):
    """发送验证码请求模型

    用于验证发送验证码的请求参数。
    """

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    scene: SmsScene = Field(..., description="场景")


class SmsSendResponse(BaseModel):
    """发送验证码响应模型

    返回发送结果和相关的限制信息。
    """

    expire_in: int = Field(..., description="有效期（秒）")
    cooldown: int = Field(..., description="冷却时间（秒）")


class SmsVerifyRequest(BaseModel):
    """验证验证码请求模型

    用于验证码校验的请求参数。
    """

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    code: str = Field(..., min_length=4, max_length=10, description="验证码")
    scene: SmsScene = Field(..., description="场景")
