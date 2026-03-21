"""
阿里云短信客户端测试
===================

测试阿里云短信发送功能。
"""

from unittest.mock import MagicMock, patch

import pytest

from src.api.config import APIConfig
from src.infrastructure.aliyun_sms_client import (
    AliyunSmsClient,
    SmsSendResult,
    get_aliyun_sms_client,
    init_aliyun_sms_client,
)


class TestSmsSendResult:
    """短信发送结果测试"""

    def test_create_success_result(self) -> None:
        """测试创建成功结果"""
        result = SmsSendResult(success=True, biz_id="123456")
        assert result.success is True
        assert result.biz_id == "123456"
        assert result.error_code is None
        assert result.error_message is None

    def test_create_failure_result(self) -> None:
        """测试创建失败结果"""
        result = SmsSendResult(
            success=False,
            error_code="SignatureDoesNotMatch",
            error_message="签名不匹配",
        )
        assert result.success is False
        assert result.biz_id is None
        assert result.error_code == "SignatureDoesNotMatch"
        assert result.error_message == "签名不匹配"


class TestAliyunSmsClient:
    """阿里云短信客户端测试"""

    @pytest.fixture
    def mock_config(self) -> APIConfig:
        """Mock 配置"""
        return APIConfig(
            ALIYUN_ACCESS_KEY_ID="test-key-id",
            ALIYUN_ACCESS_KEY_SECRET="test-key-secret",
            SMS_SIGN_NAME="户外规划助手",
            SMS_TEMPLATE_REGISTER="SMS_123456",
            SMS_TEMPLATE_LOGIN="SMS_234567",
            SMS_TEMPLATE_BIND="SMS_345678",
            SMS_TEMPLATE_UNBIND="SMS_456789",
            SMS_TEMPLATE_RESET_PASSWORD="SMS_567890",
        )

    @pytest.fixture
    def mock_mode_config(self) -> APIConfig:
        """Mock 模式配置（无 AccessKey）"""
        return APIConfig(
            ALIYUN_ACCESS_KEY_ID="",
            ALIYUN_ACCESS_KEY_SECRET="",
            SMS_SIGN_NAME="户外规划助手",
            SMS_TEMPLATE_REGISTER="SMS_123456",
        )

    def test_init_with_config(self, mock_config: APIConfig) -> None:
        """测试初始化"""
        client = AliyunSmsClient(mock_config)
        assert client is not None

    def test_init_with_mock_mode(self, mock_mode_config: APIConfig) -> None:
        """测试 Mock 模式初始化"""
        client = AliyunSmsClient(mock_mode_config)
        assert client is not None
        assert client._is_mock_mode() is True

    def test_is_mock_mode_true(self, mock_mode_config: APIConfig) -> None:
        """测试判断 Mock 模式（无密钥）"""
        client = AliyunSmsClient(mock_mode_config)
        assert client._is_mock_mode() is True

    def test_is_mock_mode_false(self, mock_config: APIConfig) -> None:
        """测试判断真实模式（有密钥）"""
        client = AliyunSmsClient(mock_config)
        assert client._is_mock_mode() is False

    def test_get_template_id_register(self, mock_config: APIConfig) -> None:
        """测试获取注册模板 ID"""
        client = AliyunSmsClient(mock_config)
        template_id = client.get_template_id("register")
        assert template_id == "SMS_123456"

    def test_get_template_id_login(self, mock_config: APIConfig) -> None:
        """测试获取登录模板 ID"""
        client = AliyunSmsClient(mock_config)
        template_id = client.get_template_id("login")
        assert template_id == "SMS_234567"

    def test_get_template_id_bind(self, mock_config: APIConfig) -> None:
        """测试获取绑定模板 ID"""
        client = AliyunSmsClient(mock_config)
        template_id = client.get_template_id("bind")
        assert template_id == "SMS_345678"

    def test_get_template_id_unbind(self, mock_config: APIConfig) -> None:
        """测试获取解绑模板 ID"""
        client = AliyunSmsClient(mock_config)
        template_id = client.get_template_id("unbind")
        assert template_id == "SMS_456789"

    def test_get_template_id_reset_password(self, mock_config: APIConfig) -> None:
        """测试获取重置密码模板 ID"""
        client = AliyunSmsClient(mock_config)
        template_id = client.get_template_id("reset_password")
        assert template_id == "SMS_567890"

    def test_get_template_id_invalid_scene(self, mock_config: APIConfig) -> None:
        """测试获取无效场景模板 ID"""
        client = AliyunSmsClient(mock_config)
        template_id = client.get_template_id("invalid_scene")
        assert template_id == ""

    def test_send_verification_code_mock_mode(self, mock_mode_config: APIConfig) -> None:
        """测试 Mock 模式发送验证码"""
        client = AliyunSmsClient(mock_mode_config)
        result = client.send_verification_code("13800138000", "123456", "SMS_123456")
        assert result.success is True
        assert result.biz_id == "MOCK_BIZ_ID"
        assert result.error_code is None
        assert result.error_message is None

    @patch.object(AliyunSmsClient, "_send_sms_via_aliyun")
    def test_send_verification_code_success(self, mock_send: MagicMock, mock_config: APIConfig) -> None:
        """测试发送验证码成功（真实模式）"""
        # Mock 内部方法返回成功
        mock_send.return_value = SmsSendResult(
            success=True,
            biz_id="123456789",
        )

        client = AliyunSmsClient(mock_config)
        result = client.send_verification_code("13800138000", "123456", "SMS_123456")

        assert result.success is True
        assert result.biz_id == "123456789"
        assert result.error_code is None
        assert result.error_message is None

    @patch.object(AliyunSmsClient, "_send_sms_via_aliyun")
    def test_send_verification_code_failure(self, mock_send: MagicMock, mock_config: APIConfig) -> None:
        """测试发送验证码失败（真实模式）"""
        # Mock 内部方法返回失败
        mock_send.return_value = SmsSendResult(
            success=False,
            error_code="SignatureDoesNotMatch",
            error_message="签名不匹配",
        )

        client = AliyunSmsClient(mock_config)
        result = client.send_verification_code("13800138000", "123456", "SMS_123456")

        assert result.success is False
        assert result.biz_id is None
        assert result.error_code == "SignatureDoesNotMatch"
        assert result.error_message == "签名不匹配"

    @patch.object(AliyunSmsClient, "_send_sms_via_aliyun")
    def test_send_verification_code_exception(self, mock_send: MagicMock, mock_config: APIConfig) -> None:
        """测试发送验证码异常（真实模式）"""
        # Mock 内部方法返回异常错误
        mock_send.return_value = SmsSendResult(
            success=False,
            error_code="EXCEPTION",
            error_message="网络错误",
        )

        client = AliyunSmsClient(mock_config)
        result = client.send_verification_code("13800138000", "123456", "SMS_123456")

        assert result.success is False
        assert result.biz_id is None
        assert result.error_code == "EXCEPTION"
        assert result.error_message == "网络错误"

    def test_send_verification_code_invalid_phone(self, mock_mode_config: APIConfig) -> None:
        """测试无效手机号"""
        client = AliyunSmsClient(mock_mode_config)
        result = client.send_verification_code("12345", "123456", "SMS_123456")
        assert result.success is False
        assert result.error_code == "INVALID_PHONE"
        assert result.error_message is not None
        assert "手机号格式错误" in result.error_message

    def test_send_verification_code_empty_phone(self, mock_mode_config: APIConfig) -> None:
        """测试空手机号"""
        client = AliyunSmsClient(mock_mode_config)
        result = client.send_verification_code("", "123456", "SMS_123456")
        assert result.success is False
        assert result.error_code == "INVALID_PHONE"

    def test_send_verification_code_empty_code(self, mock_mode_config: APIConfig) -> None:
        """测试空验证码"""
        client = AliyunSmsClient(mock_mode_config)
        result = client.send_verification_code("13800138000", "", "SMS_123456")
        assert result.success is False
        assert result.error_code == "INVALID_CODE"

    def test_send_verification_code_empty_template(self, mock_mode_config: APIConfig) -> None:
        """测试空模板 ID"""
        client = AliyunSmsClient(mock_mode_config)
        result = client.send_verification_code("13800138000", "123456", "")
        assert result.success is False
        assert result.error_code == "INVALID_TEMPLATE"


class TestGlobalAliyunSmsClient:
    """全局短信客户端测试"""

    def test_init_aliyun_sms_client(self) -> None:
        """测试初始化全局客户端"""
        config = APIConfig(
            ALIYUN_ACCESS_KEY_ID="test-key-id",
            ALIYUN_ACCESS_KEY_SECRET="test-key-secret",
            SMS_SIGN_NAME="户外规划助手",
            SMS_TEMPLATE_REGISTER="SMS_123456",
        )
        client = init_aliyun_sms_client(config)
        assert isinstance(client, AliyunSmsClient)
        assert get_aliyun_sms_client() is client

    def test_get_aliyun_sms_client_before_init(self) -> None:
        """测试在初始化前获取客户端"""
        # 重置全局变量
        import src.infrastructure.aliyun_sms_client as sms_module
        sms_module.aliyun_sms_client = None
        with pytest.raises(ValueError, match="短信客户端未初始化"):
            get_aliyun_sms_client()

    def test_init_multiple_times(self) -> None:
        """测试多次初始化"""
        config1 = APIConfig(
            ALIYUN_ACCESS_KEY_ID="key1",
            ALIYUN_ACCESS_KEY_SECRET="secret1",
            SMS_SIGN_NAME="签名1",
            SMS_TEMPLATE_REGISTER="SMS_111",
        )
        config2 = APIConfig(
            ALIYUN_ACCESS_KEY_ID="key2",
            ALIYUN_ACCESS_KEY_SECRET="secret2",
            SMS_SIGN_NAME="签名2",
            SMS_TEMPLATE_REGISTER="SMS_222",
        )

        client1 = init_aliyun_sms_client(config1)
        client2 = init_aliyun_sms_client(config2)

        # 应该返回同一个实例
        assert get_aliyun_sms_client() is client2
        assert get_aliyun_sms_client() is not client1
