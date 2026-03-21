"""
短信验证码服务
==============
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger

from src.infrastructure.aliyun_sms_client import AliyunSmsClient
from src.repositories.sms_code_repo import SmsCodeRepository
from src.repositories.sms_log_repo import SmsLogRepository

if TYPE_CHECKING:
    from src.api.config import APIConfig


# 手机号正则表达式（中国大陆）
_PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


@dataclass
class SendCodeResult:
    """发送验证码结果"""

    success: bool
    expire_in: int = 0
    cooldown: int = 0
    error_code: str | None = None
    error_message: str | None = None


@dataclass
class RateLimitResult:
    """频率限制检查结果"""

    can_send: bool
    remaining: int  # 今日剩余次数
    cooldown_remaining: int  # 冷却剩余秒数


class SmsService:
    """短信验证码服务

    整合验证码仓库和短信客户端，提供完整的验证码发送和验证功能。

    Args:
        sms_code_repo: 验证码仓库
        sms_log_repo: 短信日志仓库
        sms_client: 短信客户端
        config: API 配置
    """

    def __init__(
        self,
        sms_code_repo: SmsCodeRepository,
        sms_log_repo: SmsLogRepository,
        sms_client: AliyunSmsClient,
        config: "APIConfig",
    ) -> None:
        """初始化服务

        Args:
            sms_code_repo: 验证码仓库
            sms_log_repo: 短信日志仓库
            sms_client: 短信客户端
            config: API 配置
        """
        self._sms_code_repo = sms_code_repo
        self._sms_log_repo = sms_log_repo
        self._sms_client = sms_client
        self._config = config

    def send_code(self, phone: str, scene: str, ip: str | None = None) -> SendCodeResult:
        """发送验证码

        Args:
            phone: 手机号
            scene: 使用场景
            ip: 请求 IP 地址

        Returns:
            发送结果
        """
        # 1. 检查手机号格式
        if not self._validate_phone(phone):
            logger.warning(f"无效的手机号: {phone}")
            return SendCodeResult(success=False, error_code="INVALID_PHONE", error_message="手机号格式错误")

        # 2. 检查冷却时间
        cooldown = self._check_cooldown(phone)
        if cooldown > 0:
            logger.info(f"手机号 {phone} 冷却中，剩余 {cooldown} 秒")
            return SendCodeResult(
                success=False,
                error_code="RATE_LIMITED",
                error_message=f"请 {cooldown} 秒后重试",
                cooldown=cooldown,
            )

        # 3. 检查每日限制
        can_send, remaining = self._check_daily_limit(phone)
        if not can_send:
            logger.warning(f"手机号 {phone} 今日发送次数已达上限")
            return SendCodeResult(
                success=False,
                error_code="DAILY_LIMIT_EXCEEDED",
                error_message="今日发送次数已达上限",
            )

        # 4. 生成验证码
        code = self._generate_code()

        # 5. 发送短信
        template_id = self._sms_client.get_template_id(scene)
        send_result = self._sms_client.send_verification_code(phone, code, template_id)

        # 6. 记录日志
        self._sms_log_repo.create(phone, scene, ip, send_result.success, send_result.error_message)

        # 7. 如果发送成功，保存验证码
        if send_result.success:
            # 将枚举转换为字符串存储
            scene_str = scene.value if hasattr(scene, 'value') else scene
            self._sms_code_repo.create(phone, code, scene_str, self._config.SMS_EXPIRE_SECONDS)
            logger.info(f"验证码发送成功: {phone}, 场景: {scene}")
        else:
            logger.warning(f"验证码发送失败: {phone}, 错误: {send_result.error_message}")

        return SendCodeResult(
            success=send_result.success,
            expire_in=self._config.SMS_EXPIRE_SECONDS if send_result.success else 0,
            cooldown=self._config.SMS_COOLDOWN_SECONDS,
            error_code=send_result.error_code,
            error_message=send_result.error_message,
        )

    def verify_code(self, phone: str, code: str, scene: str) -> bool:
        """验证验证码

        Args:
            phone: 手机号
            code: 验证码
            scene: 使用场景

        Returns:
            验证成功返回 True，否则返回 False
        """
        result = self._sms_code_repo.verify_code(phone, code, scene)
        if result:
            logger.info(f"验证码验证成功: {phone}, 场景: {scene}")
        else:
            logger.warning(f"验证码验证失败: {phone}, 场景: {scene}")
        return result

    def check_rate_limit(self, phone: str) -> RateLimitResult:
        """检查发送频率限制

        Args:
            phone: 手机号

        Returns:
            频率限制检查结果
        """
        # 检查冷却时间
        cooldown_remaining = self._check_cooldown(phone)
        if cooldown_remaining > 0:
            return RateLimitResult(can_send=False, remaining=0, cooldown_remaining=cooldown_remaining)

        # 检查每日限制
        today_count = self._sms_log_repo.count_today_by_phone(phone)
        remaining = max(0, self._config.SMS_DAILY_LIMIT - today_count)

        if remaining == 0:
            return RateLimitResult(can_send=False, remaining=0, cooldown_remaining=0)

        return RateLimitResult(can_send=True, remaining=remaining, cooldown_remaining=0)

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

    def _generate_code(self) -> str:
        """生成验证码

        Returns:
            随机验证码
        """
        import secrets

        # 使用 secrets 模块生成安全的随机验证码
        # 生成范围: [10^(n-1), 10^n - 1]
        code_length = self._config.SMS_CODE_LENGTH
        min_code = 10 ** (code_length - 1)
        max_code = (10**code_length) - 1
        return str(secrets.randbelow(max_code - min_code + 1) + min_code)

    def _check_cooldown(self, phone: str) -> int:
        """检查冷却时间

        Args:
            phone: 手机号

        Returns:
            剩余冷却秒数，0 表示可以发送
        """
        latest_time = self._sms_log_repo.get_latest_by_phone(phone)
        if latest_time is None:
            return 0

        elapsed = (datetime.now() - latest_time).total_seconds()
        cooldown = self._config.SMS_COOLDOWN_SECONDS - int(elapsed)
        return max(0, cooldown)

    def _check_daily_limit(self, phone: str) -> tuple[bool, int]:
        """检查每日限制

        Args:
            phone: 手机号

        Returns:
            (是否可以发送, 剩余次数)
        """
        today_count = self._sms_log_repo.count_today_by_phone(phone)
        remaining = self._config.SMS_DAILY_LIMIT - today_count
        return remaining > 0, remaining
