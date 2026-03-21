"""
用户 ORM 模型
==============

定义用户表的数据库映射。
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.mysql_client import Base


class User(Base):
    """用户表 ORM 模型

    Attributes:
        id: 用户 ID（主键，自增）
        username: 用户名（可选，唯一）
        phone: 手机号（可选，唯一）
        password_hash: 密码哈希（可选）
        role: 角色（默认: user）
        status: 状态（默认: active）
        created_at: 创建时间
        updated_at: 更新时间
        last_login_at: 最后登录时间
        deleted_at: 软删除时间
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, phone={self.phone})"
