"""
短信发送日志 ORM 模型
======================
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.mysql_client import Base


class SmsSendLog(Base):
    """短信发送日志表 ORM 模型

    用于记录短信发送历史，支持频率限制。

    Attributes:
        id: 主键（自增）
        phone: 手机号
        scene: 使用场景
        ip: 请求 IP 地址（可选）
        success: 是否成功（0: 失败, 1: 成功）
        error_msg: 错误信息（可选）
        created_at: 创建时间
    """

    __tablename__ = "sms_send_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scene: Mapped[str] = mapped_column(String(20), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    success: Mapped[int] = mapped_column(Integer, nullable=False)
    error_msg: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"SmsSendLog(id={self.id}, phone={self.phone}, scene={self.scene}, success={self.success})"
