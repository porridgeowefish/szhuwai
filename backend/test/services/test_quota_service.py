"""
额度服务单元测试
================
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.schemas.quota import QuotaInfo
from src.services.quota_service import QuotaCheckResult, QuotaService


class TestQuotaService:
    """额度服务测试"""

    def test_get_quota_info_normal_user(self) -> None:
        """测试普通用户额度信息"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        # 模拟普通用户
        mock_user = MagicMock()
        mock_user.role = "user"
        mock_user_repo.get_by_id.return_value = mock_user

        # 模拟已使用 1 次
        mock_quota_repo.get_usage.return_value = 1

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service.get_quota_info(1)

        # Assert
        assert isinstance(result, QuotaInfo)
        assert result.used == 1
        assert result.total == 2
        assert result.remaining == 1
        assert result.is_unlimited is False
        mock_user_repo.get_by_id.assert_called_once_with(1)
        mock_quota_repo.get_usage.assert_called_once_with(1)

    def test_get_quota_info_admin_user(self) -> None:
        """测试管理员额度信息（无限制）"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        # 模拟管理员用户
        mock_user = MagicMock()
        mock_user.role = "admin"
        mock_user_repo.get_by_id.return_value = mock_user

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service.get_quota_info(1)

        # Assert
        assert isinstance(result, QuotaInfo)
        assert result.used == 0
        assert result.total == -1
        assert result.remaining == -1
        assert result.is_unlimited is True
        # 管理员不应调用 quota_repo
        mock_quota_repo.get_usage.assert_not_called()

    def test_get_quota_info_user_not_found(self) -> None:
        """测试用户不存在"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()
        mock_user_repo.get_by_id.return_value = None

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="用户不存在"):
            service.get_quota_info(999)

    def test_check_quota_available(self) -> None:
        """测试检查额度充足"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        mock_user = MagicMock()
        mock_user.role = "user"
        mock_user_repo.get_by_id.return_value = mock_user
        mock_quota_repo.get_usage.return_value = 1

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service.check_quota(1)

        # Assert
        assert isinstance(result, QuotaCheckResult)
        assert result.has_quota is True
        assert result.remaining == 1
        assert result.used == 1

    def test_check_quota_exhausted(self) -> None:
        """测试检查额度耗尽"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        mock_user = MagicMock()
        mock_user.role = "user"
        mock_user_repo.get_by_id.return_value = mock_user
        mock_quota_repo.get_usage.return_value = 2  # 已用完

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service.check_quota(1)

        # Assert
        assert isinstance(result, QuotaCheckResult)
        assert result.has_quota is False
        assert result.remaining == 0
        assert result.used == 2

    def test_check_quota_admin(self) -> None:
        """测试管理员检查额度（始终有额度）"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        mock_user = MagicMock()
        mock_user.role = "admin"
        mock_user_repo.get_by_id.return_value = mock_user

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service.check_quota(1)

        # Assert
        assert isinstance(result, QuotaCheckResult)
        assert result.has_quota is True
        assert result.remaining == -1

    def test_consume_quota_success(self) -> None:
        """测试消耗额度成功"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        mock_user = MagicMock()
        mock_user.role = "user"
        mock_user_repo.get_by_id.return_value = mock_user
        mock_quota_repo.get_usage.return_value = 1  # 还有 1 次
        mock_quota_repo.increment_usage.return_value = 2

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service.consume_quota(1)

        # Assert
        assert result is True
        mock_quota_repo.increment_usage.assert_called_once_with(1)

    def test_consume_quota_failed(self) -> None:
        """测试消耗额度失败（额度不足）"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        mock_user = MagicMock()
        mock_user.role = "user"
        mock_user_repo.get_by_id.return_value = mock_user
        mock_quota_repo.get_usage.return_value = 2  # 已用完

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service.consume_quota(1)

        # Assert
        assert result is False
        mock_quota_repo.increment_usage.assert_not_called()

    def test_consume_quota_admin(self) -> None:
        """测试管理员消耗额度（始终成功）"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        mock_user = MagicMock()
        mock_user.role = "admin"
        mock_user_repo.get_by_id.return_value = mock_user

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service.consume_quota(1)

        # Assert
        assert result is True
        # 管理员不应调用 increment_usage
        mock_quota_repo.increment_usage.assert_not_called()

    def test_consume_quota_user_not_found(self) -> None:
        """测试用户不存在时消耗额度"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()
        mock_user_repo.get_by_id.return_value = None

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service.consume_quota(999)

        # Assert
        assert result is False

    def test_get_reset_time(self) -> None:
        """测试获取重置时间"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service.get_reset_time()

        # Assert
        assert isinstance(result, datetime)
        # 验证是明天
        tomorrow = date.today() + timedelta(days=1)
        assert result.date() == tomorrow
        # 验证是 0 点
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_is_admin(self) -> None:
        """测试管理员检查"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act & Assert - 普通用户
        mock_user = MagicMock()
        mock_user.role = "user"
        mock_user_repo.get_by_id.return_value = mock_user
        assert service._is_admin(1) is False

        # Act & Assert - 管理员
        mock_user.role = "admin"
        assert service._is_admin(1) is True

    def test_get_user_role(self) -> None:
        """测试获取用户角色"""
        # Arrange
        mock_quota_repo = MagicMock()
        mock_user_repo = MagicMock()

        mock_user = MagicMock()
        mock_user.role = "admin"
        mock_user_repo.get_by_id.return_value = mock_user

        service = QuotaService(
            quota_repo=mock_quota_repo,
            user_repo=mock_user_repo,
        )

        # Act
        result = service._get_user_role(1)

        # Assert
        assert result == "admin"
        mock_user_repo.get_by_id.assert_called_once_with(1)
