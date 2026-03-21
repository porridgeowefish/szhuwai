"""
额度业务服务
============
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from src.repositories.quota_repo import QuotaRepository
from src.repositories.user_repo import UserRepository
from src.schemas.quota import QuotaInfo


@dataclass
class QuotaCheckResult:
    """额度检查结果"""

    has_quota: bool
    remaining: int
    used: int
    message: str | None = None


class QuotaService:
    """额度业务服务

    提供额度查询、检查和扣减功能。
    管理员拥有无限制额度。

    Attributes:
        quota_repo: 额度数据仓库
        user_repo: 用户数据仓库
        DEFAULT_DAILY_QUOTA: 默认每日额度
    """

    DEFAULT_DAILY_QUOTA = 2

    def __init__(
        self,
        quota_repo: QuotaRepository,
        user_repo: UserRepository,
    ) -> None:
        """初始化服务

        Args:
            quota_repo: 额度数据仓库
            user_repo: 用户数据仓库
        """
        self.quota_repo = quota_repo
        self.user_repo = user_repo

    def get_quota_info(self, user_id: int) -> QuotaInfo:
        """获取用户额度信息

        管理员返回 remaining=-1 表示无限制。

        Args:
            user_id: 用户 ID

        Returns:
            QuotaInfo: 额度信息

        Raises:
            ValueError: 用户不存在
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        # 管理员返回无限制
        if user.role == "admin":
            return QuotaInfo(
                used=0,
                total=-1,
                remaining=-1,
                reset_at=self.get_reset_time(),
            )

        # 普通用户查询当日使用量
        used = self.quota_repo.get_usage(user_id)
        return QuotaInfo(
            used=used,
            total=self.DEFAULT_DAILY_QUOTA,
            remaining=max(0, self.DEFAULT_DAILY_QUOTA - used),
            reset_at=self.get_reset_time(),
        )

    def check_quota(self, user_id: int) -> QuotaCheckResult:
        """检查用户是否有剩余额度

        Args:
            user_id: 用户 ID

        Returns:
            QuotaCheckResult: 检查结果
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return QuotaCheckResult(
                has_quota=False,
                remaining=0,
                used=0,
                message="用户不存在",
            )

        # 管理员无限制
        if user.role == "admin":
            return QuotaCheckResult(
                has_quota=True,
                remaining=-1,
                used=0,
            )

        # 普通用户检查
        used = self.quota_repo.get_usage(user_id)
        remaining = max(0, self.DEFAULT_DAILY_QUOTA - used)

        return QuotaCheckResult(
            has_quota=remaining > 0,
            remaining=remaining,
            used=used,
        )

    def consume_quota(self, user_id: int) -> bool:
        """消耗一次额度

        Args:
            user_id: 用户 ID

        Returns:
            是否消耗成功（额度不足时返回 False）
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False

        # 管理员无限制
        if user.role == "admin":
            return True

        # 检查额度
        check_result = self.check_quota(user_id)
        if not check_result.has_quota:
            return False

        # 扣减额度
        self.quota_repo.increment_usage(user_id)
        return True

    def get_reset_time(self) -> datetime:
        """获取下次重置时间（明天 0 点）

        Returns:
            datetime: 重置时间
        """
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

    def _is_admin(self, user_id: int) -> bool:
        """检查用户是否为管理员

        Args:
            user_id: 用户 ID

        Returns:
            是否为管理员
        """
        return self._get_user_role(user_id) == "admin"

    def _get_user_role(self, user_id: int) -> str:
        """获取用户角色

        Args:
            user_id: 用户 ID

        Returns:
            用户角色
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return "user"
        return str(user.role)
