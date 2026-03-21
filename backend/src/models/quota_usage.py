"""
额度 ORM 模型
==============

定义额度使用表的数据库映射。
"""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.mysql_client import Base

if TYPE_CHECKING:
    from src.models.user import User


class QuotaUsage(Base):
    """额度使用表 ORM 模型

    记录用户每日的使用额度情况。

    Attributes:
        id: 主键 ID
        user_id: 用户 ID（外键）
        usage_date: 使用日期
        usage_count: 使用次数
        created_at: 创建时间
        updated_at: 更新时间
        user: 关联的用户
    """

    __tablename__ = "quota_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uk_user_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    usage_date: Mapped[date] = mapped_column(Date, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # 关联
    user: Mapped["User"] = relationship(back_populates="quota_usages")

    def __repr__(self) -> str:
        return (
            f"QuotaUsage(id={self.id}, user_id={self.user_id}, "
            f"usage_date={self.usage_date}, usage_count={self.usage_count})"
        )
