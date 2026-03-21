"""
SmsService 单元测试
===================
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.services.sms_service import RateLimitResult, SendCodeResult, SmsService


class TestSmsService:
    """短信验证码服务测试"""

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.SMS_CODE_LENGTH = 6
        config.SMS_EXPIRE_SECONDS = 300
        config.SMS_COOLDOWN_SECONDS = 60
        config.SMS_DAILY_LIMIT = 10
        return config

    @pytest.fixture
    def mock_repos(self) -> tuple[MagicMock, MagicMock]:
        """创建模拟仓库"""
        sms_code_repo = MagicMock()
        sms_log_repo = MagicMock()
        return sms_code_repo, sms_log_repo

    @pytest.fixture
    def mock_sms_client(self) -> MagicMock:
        """创建模拟短信客户端"""
        client = MagicMock()
        client.send_verification_code.return_value = MagicMock(
            success=True, biz_id="TEST_BIZ_ID", error_code=None, error_message=None
        )
        client.get_template_id.return_value = "TEST_TEMPLATE"
        return client

    @pytest.fixture
    def sms_service(
        self, mock_config: MagicMock, mock_repos: tuple[MagicMock, MagicMock], mock_sms_client: MagicMock
    ) -> SmsService:
        """创建 SmsService 实例"""
        sms_code_repo, sms_log_repo = mock_repos
        return SmsService(sms_code_repo, sms_log_repo, mock_sms_client, mock_config)

    def test_send_code_success(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock]) -> None:
        """测试发送成功"""
        sms_code_repo, sms_log_repo = mock_repos

        # 模拟仓库返回值
        sms_log_repo.count_today_by_phone.return_value = 5  # 今日已发送 5 次
        sms_log_repo.get_latest_by_phone.return_value = datetime.now() - timedelta(seconds=120)  # 2分钟前发送过

        result = sms_service.send_code("13800138000", "login", "127.0.0.1")

        # 显式检查返回类型
        assert isinstance(result, SendCodeResult)
        assert result.success is True
        assert result.expire_in == 300
        assert result.cooldown == 60
        assert result.error_code is None
        assert result.error_message is None

        # 验证调用了保存验证码
        sms_code_repo.create.assert_called_once()
        call_args = sms_code_repo.create.call_args
        assert call_args[0][0] == "13800138000"  # phone
        assert call_args[0][1].isdigit()  # code 是数字
        assert len(call_args[0][1]) == 6  # code 长度为 6
        assert call_args[0][2] == "login"  # scene
        assert call_args[0][3] == 300  # expire_seconds

        # 验证记录了日志
        sms_log_repo.create.assert_called_once_with("13800138000", "login", "127.0.0.1", True, None)

    def test_send_code_rate_limited_cooldown(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock]) -> None:
        """测试冷却时间限制"""
        sms_code_repo, sms_log_repo = mock_repos

        # 模拟 30 秒前刚发送过
        sms_log_repo.get_latest_by_phone.return_value = datetime.now() - timedelta(seconds=30)

        result = sms_service.send_code("13800138000", "login", "127.0.0.1")

        assert result.success is False
        assert result.error_code == "RATE_LIMITED"
        assert "30" in result.error_message or "29" in result.error_message  # 剩余秒数
        assert result.cooldown > 0

        # 验证没有保存验证码
        sms_code_repo.create.assert_not_called()

    def test_send_code_daily_limit_exceeded(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock]) -> None:
        """测试每日上限"""
        sms_code_repo, sms_log_repo = mock_repos

        # 模拟今日已发送 10 次（达到上限）
        sms_log_repo.count_today_by_phone.return_value = 10
        sms_log_repo.get_latest_by_phone.return_value = datetime.now() - timedelta(seconds=120)

        result = sms_service.send_code("13800138000", "login", "127.0.0.1")

        assert result.success is False
        assert result.error_code == "DAILY_LIMIT_EXCEEDED"
        assert "上限" in result.error_message

        # 验证没有保存验证码
        sms_code_repo.create.assert_not_called()

    def test_send_code_invalid_phone(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock]) -> None:
        """测试无效手机号"""
        sms_code_repo, _ = mock_repos

        # 测试各种无效手机号
        invalid_phones = ["12345", "1380013800", "138001380001", "abc12345678", "", "1380013800a"]

        for phone in invalid_phones:
            result = sms_service.send_code(phone, "login", "127.0.0.1")
            assert result.success is False
            assert result.error_code == "INVALID_PHONE"

        # 验证没有保存验证码
        sms_code_repo.create.assert_not_called()

    def test_send_code_client_error(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock], mock_sms_client: MagicMock) -> None:
        """测试短信客户端返回错误"""
        sms_code_repo, sms_log_repo = mock_repos

        # 模拟客户端返回错误
        mock_sms_client.send_verification_code.return_value = MagicMock(
            success=False, error_code="NETWORK_ERROR", error_message="网络错误"
        )

        sms_log_repo.count_today_by_phone.return_value = 0
        sms_log_repo.get_latest_by_phone.return_value = None

        result = sms_service.send_code("13800138000", "login", "127.0.0.1")

        assert result.success is False
        assert result.error_code == "NETWORK_ERROR"
        assert result.error_message == "网络错误"

        # 验证没有保存验证码
        sms_code_repo.create.assert_not_called()

        # 验证记录了失败日志
        sms_log_repo.create.assert_called_once_with("13800138000", "login", "127.0.0.1", False, "网络错误")

    def test_verify_code_success(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock]) -> None:
        """测试验证成功"""
        sms_code_repo, _ = mock_repos

        # 模拟验证码验证成功
        sms_code_repo.verify_code.return_value = True

        result = sms_service.verify_code("13800138000", "123456", "login")

        assert result is True
        sms_code_repo.verify_code.assert_called_once_with("13800138000", "123456", "login")

    def test_verify_code_wrong(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock]) -> None:
        """测试验证失败（错误验证码）"""
        sms_code_repo, _ = mock_repos

        # 模拟验证码验证失败
        sms_code_repo.verify_code.return_value = False

        result = sms_service.verify_code("13800138000", "wrong_code", "login")

        assert result is False

    def test_check_rate_limit_can_send(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock]) -> None:
        """测试频率检查通过"""
        _, sms_log_repo = mock_repos

        # 模拟可以发送
        sms_log_repo.count_today_by_phone.return_value = 3
        sms_log_repo.get_latest_by_phone.return_value = datetime.now() - timedelta(seconds=120)

        result = sms_service.check_rate_limit("13800138000")

        # 显式检查返回类型
        assert isinstance(result, RateLimitResult)
        assert result.can_send is True
        assert result.remaining == 7  # 10 - 3 = 7
        assert result.cooldown_remaining == 0

    def test_check_rate_limit_cooldown(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock]) -> None:
        """测试频率检查冷却中"""
        _, sms_log_repo = mock_repos

        # 模拟冷却中
        sms_log_repo.count_today_by_phone.return_value = 0
        sms_log_repo.get_latest_by_phone.return_value = datetime.now() - timedelta(seconds=30)

        result = sms_service.check_rate_limit("13800138000")

        assert result.can_send is False
        assert result.cooldown_remaining > 0
        assert result.cooldown_remaining <= 30

    def test_check_rate_limit_daily_exceeded(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock]) -> None:
        """测试频率检查每日已达上限"""
        _, sms_log_repo = mock_repos

        # 模拟已达上限
        sms_log_repo.count_today_by_phone.return_value = 10
        sms_log_repo.get_latest_by_phone.return_value = datetime.now() - timedelta(seconds=120)

        result = sms_service.check_rate_limit("13800138000")

        assert result.can_send is False
        assert result.remaining == 0
        assert result.cooldown_remaining == 0

    def test_generate_code_length(self, sms_service: SmsService, mock_config: MagicMock) -> None:
        """测试验证码长度"""
        # 测试不同长度
        mock_config.SMS_CODE_LENGTH = 4
        code1 = sms_service._generate_code()
        assert len(code1) == 4
        assert code1.isdigit()

        mock_config.SMS_CODE_LENGTH = 8
        code2 = sms_service._generate_code()
        assert len(code2) == 8
        assert code2.isdigit()

    def test_send_code_first_time(self, sms_service: SmsService, mock_repos: tuple[MagicMock, MagicMock]) -> None:
        """测试首次发送（无历史记录）"""
        sms_code_repo, sms_log_repo = mock_repos

        # 模拟无历史记录
        sms_log_repo.count_today_by_phone.return_value = 0
        sms_log_repo.get_latest_by_phone.return_value = None

        result = sms_service.send_code("13800138000", "login", "127.0.0.1")

        assert result.success is True
        sms_code_repo.create.assert_called_once()
