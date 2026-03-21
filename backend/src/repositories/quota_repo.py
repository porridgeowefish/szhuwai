"""
额度数据仓库
============

提供额度使用的数据访问操作。
"""

from datetime import date

from loguru import logger
from sqlalchemy.orm import Session

from src.models.quota_usage import QuotaUsage


class QuotaRepository:
    """额度数据仓库

    管理用户每日额度的数据访问。

    Attributes:
        session: 数据库会话
        DEFAULT_DAILY_QUOTA: 默认每日额度
    """

    DEFAULT_DAILY_QUOTA = 2

    def __init__(self, session: Session) -> None:
        """初始化仓库

        Args:
            session: SQLAlchemy 会话对象
        """
        self.session = session

    def get_or_create(
        self, user_id: int, usage_date: date | None = None
    ) -> QuotaUsage:
        """获取或创建当日额度记录

        如果指定日期的记录不存在，则创建新记录。

        Args:
            user_id: 用户 ID
            usage_date: 使用日期，默认为今天

        Returns:
            QuotaUsage: 额度记录
        """
        if usage_date is None:
            usage_date = date.today()

        # 尝试获取已有记录
        quota = (
            self.session.query(QuotaUsage)
            .filter(
                QuotaUsage.user_id == user_id,
                QuotaUsage.usage_date == usage_date,
            )
            .first()
        )

        # 不存在则创建
        if quota is None:
            quota = QuotaUsage(
                user_id=user_id,
                usage_date=usage_date,
                usage_count=0,
            )
            self.session.add(quota)
            self.session.flush()
            logger.debug(
                f"创建新额度记录: user_id={user_id}, date={usage_date}"
            )

        return quota

    def get_usage(self, user_id: int, usage_date: date | None = None) -> int:
        """获取当日已使用次数

        Args:
            user_id: 用户 ID
            usage_date: 使用日期，默认为今天

        Returns:
            int: 已使用次数，无记录时返回 0
        """
        if usage_date is None:
            usage_date = date.today()

        quota = (
            self.session.query(QuotaUsage)
            .filter(
                QuotaUsage.user_id == user_id,
                QuotaUsage.usage_date == usage_date,
            )
            .first()
        )

        return quota.usage_count if quota else 0

    def increment_usage(
        self, user_id: int, usage_date: date | None = None
    ) -> int:
        """增加使用次数

        原子性操作，确保并发安全。

        Args:
            user_id: 用户 ID
            usage_date: 使用日期，默认为今天

        Returns:
            int: 增加后的使用次数
        """
        if usage_date is None:
            usage_date = date.today()

        quota = self.get_or_create(user_id, usage_date)
        quota.usage_count += 1
        self.session.flush()

        logger.debug(
            f"额度使用增加: user_id={user_id}, date={usage_date}, count={quota.usage_count}"
        )
        return quota.usage_count

    def check_quota(
        self, user_id: int, max_count: int = DEFAULT_DAILY_QUOTA
    ) -> tuple[bool, int]:
        """检查是否有剩余额度

        Args:
            user_id: 用户 ID
            max_count: 最大额度，默认为 DEFAULT_DAILY_QUOTA

        Returns:
            (是否有剩余, 剩余次数): 元组
        """
        usage = self.get_usage(user_id)
        remaining = max_count - usage

        if remaining < 0:
            remaining = 0

        return remaining > 0, remaining

    def reset_if_new_day(self, user_id: int) -> bool:
        """如果是新的一天，创建新的记录

        检查今天是否已有记录，没有则创建。

        Args:
            user_id: 用户 ID

        Returns:
            bool: 是否创建了新记录
        """
        today = date.today()

        # 检查今天是否已有记录
        existing = (
            self.session.query(QuotaUsage)
            .filter(
                QuotaUsage.user_id == user_id,
                QuotaUsage.usage_date == today,
            )
            .first()
        )

        if existing is None:
            # 创建新记录
            self.get_or_create(user_id, today)
            logger.debug(f"新的一天，创建额度记录: user_id={user_id}, date={today}")
            return True

        return False
