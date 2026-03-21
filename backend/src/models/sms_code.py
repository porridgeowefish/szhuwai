"""
短信验证码 ORM 模型
====================
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.mysql_client import Base


class SmsCode(Base):
    """验证码表 ORM 模型

    用于存储短信验证码及其状态。

    Attributes:
        id: 主键（自增）
        phone: 手机号
        code: 验证码
        scene: 使用场景（register/login/bind/unbind/reset_password）
        used: 是否已使用（0: 未使用, 1: 已使用）
        expire_at: 过期时间
        created_at: 创建时间
    """

    __tablename__ = "sms_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    scene: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"SmsCode(id={self.id}, phone={self.phone}, scene={self.scene}, used={self.used})"
