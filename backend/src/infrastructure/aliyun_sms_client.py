"""
阿里云短信客户端模块
==================

提供阿里云短信发送功能，支持 Mock 模式用于开发测试。
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from src.api.config import APIConfig


# 手机号正则表达式（中国大陆）
_PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


@dataclass
class SmsSendResult:
    """短信发送结果"""

    success: bool
    biz_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class AliyunSmsClient:
    """阿里云短信客户端

    支持两种模式：
    - 真实模式：使用真实的阿里云短信服务发送
    - Mock 模式：不实际发送，用于开发测试
    """

    # 场景类型
    SceneType = Literal["register", "login", "bind", "unbind", "reset_password"]

    def __init__(self, config: "APIConfig") -> None:
        """初始化短信客户端

        Args:
            config: API 配置对象
        """
        self._access_key_id = config.ALIYUN_ACCESS_KEY_ID
        self._access_key_secret = config.ALIYUN_ACCESS_KEY_SECRET
        self._sign_name = config.SMS_SIGN_NAME
        self._templates = {
            "register": config.SMS_TEMPLATE_REGISTER,
            "login": config.SMS_TEMPLATE_LOGIN,
            "bind": config.SMS_TEMPLATE_BIND,
            "unbind": config.SMS_TEMPLATE_UNBIND,
            "reset_password": config.SMS_TEMPLATE_RESET_PASSWORD,
        }
        self._mock_mode = self._is_mock_mode_by_config()

    def _is_mock_mode_by_config(self) -> bool:
        """根据配置判断是否使用 Mock 模式

        当没有配置 AccessKey 时使用 Mock 模式。

        Returns:
            是否使用 Mock 模式
        """
        return not bool(self._access_key_id and self._access_key_secret)

    def _is_mock_mode(self) -> bool:
        """判断是否使用 Mock 模式

        Returns:
            是否使用 Mock 模式
        """
        return self._mock_mode

    def _validate_phone(self, phone: str) -> bool:
        """验证手机号格式

        Args:
            phone: 手机号

        Returns:
            是否有效
        """
        if not phone:
            return False
        return bool(_PHONE_PATTERN.match(phone))

    def _validate_code(self, code: str) -> bool:
        """验证验证码格式

        Args:
            code: 验证码

        Returns:
            是否有效
        """
        return bool(code and len(code) >= 4)

    def get_template_id(self, scene: str) -> str:
        """根据场景获取模板 ID

        Args:
            scene: 场景类型

        Returns:
            模板 ID，如果场景不存在则返回空字符串
        """
        return self._templates.get(scene, "")

    def send_verification_code(
        self,
        phone: str,
        code: str,
        template_id: str,
    ) -> SmsSendResult:
        """发送验证码短信

        Args:
            phone: 手机号
            code: 验证码
            template_id: 短信模板 ID

        Returns:
            发送结果
        """
        # 验证手机号
        if not self._validate_phone(phone):
            return SmsSendResult(
                success=False,
                error_code="INVALID_PHONE",
                error_message="手机号格式错误，请输入11位中国大陆手机号",
            )

        # 验证验证码
        if not self._validate_code(code):
            return SmsSendResult(
                success=False,
                error_code="INVALID_CODE",
                error_message="验证码格式错误",
            )

        # 验证模板 ID
        if not template_id:
            return SmsSendResult(
                success=False,
                error_code="INVALID_TEMPLATE",
                error_message="短信模板 ID 不能为空",
            )

        # Mock 模式：直接返回成功
        if self._is_mock_mode():
            return SmsSendResult(
                success=True,
                biz_id="MOCK_BIZ_ID",
            )

        # 真实模式：调用阿里云 SDK
        return self._send_sms_via_aliyun(phone, code, template_id)

    def _send_sms_via_aliyun(
        self,
        phone: str,
        code: str,
        template_id: str,
    ) -> SmsSendResult:
        """通过阿里云 SDK 发送短信

        Args:
            phone: 手机号
            code: 验证码
            template_id: 短信模板 ID

        Returns:
            发送结果
        """
        try:
            # 延迟导入 SDK，避免未安装时模块加载失败
            from alibabacloud_dysmsapi20170525.client import Client as DysmsClient
            from alibabacloud_dysmsapi20170525 import models as dysms_models
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_tea_util import models as util_models

            # 创建配置
            config = open_api_models.Config(
                access_key_id=self._access_key_id,
                access_key_secret=self._access_key_secret,
            )
            config.endpoint = "dysmsapi.aliyuncs.com"

            # 创建客户端
            client = DysmsClient(config)

            # 构建请求
            request = dysms_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=self._sign_name,
                template_code=template_id,
                template_param=f'{{"code":"{code}"}}',
            )

            # 设置运行时配置（超时等）
            runtime = util_models.RuntimeOptions()

            # 发送短信
            response = client.send_sms_with_options(request, runtime)

            # 检查响应
            if response.body.code == "OK":
                return SmsSendResult(
                    success=True,
                    biz_id=response.body.biz_id,
                )
            else:
                return SmsSendResult(
                    success=False,
                    error_code=response.body.code,
                    error_message=response.body.message,
                )

        except Exception as e:
            # 捕获所有异常，转换为统一错误格式
            return SmsSendResult(
                success=False,
                error_code="EXCEPTION",
                error_message=str(e),
            )


# 全局实例
aliyun_sms_client: AliyunSmsClient | None = None


def get_aliyun_sms_client() -> AliyunSmsClient:
    """获取全局短信客户端实例

    Returns:
        AliyunSmsClient 实例

    Raises:
        ValueError: 当客户端未初始化时
    """
    if aliyun_sms_client is None:
        raise ValueError("短信客户端未初始化，请先调用 init_aliyun_sms_client()")
    return aliyun_sms_client


def init_aliyun_sms_client(config: "APIConfig") -> AliyunSmsClient:
    """初始化全局短信客户端

    Args:
        config: API 配置对象

    Returns:
        初始化的 AliyunSmsClient 实例
    """
    global aliyun_sms_client
    aliyun_sms_client = AliyunSmsClient(config)
    return aliyun_sms_client
