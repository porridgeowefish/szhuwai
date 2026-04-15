"""
Redis 短信验证码服务
====================

使用 Redis 存储验证码，支持：
- 验证码 TTL 自动过期
- 原子验证（GETDEL 或 Lua 脚本）
- 验证尝试次数限制（防暴力破解）
- 每日发送限制
- 冷却时间控制
- 开发模式日志输出验证码
"""

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from loguru import logger

from src.infrastructure.redis_client import InMemoryBackend, get_redis

if TYPE_CHECKING:
    from src.api.config import APIConfig
    from src.infrastructure.aliyun_sms_client import AliyunSmsClient

# Redis key 前缀
_PREFIX_CODE = "sms:code"          # sms:code:{phone}:{scene} → 验证码
_PREFIX_DAILY = "sms:daily"        # sms:daily:{phone}:{date} → 当日发送计数
_PREFIX_COOLDOWN = "sms:cooldown"  # sms:cooldown:{phone} → 冷却标记
_PREFIX_ATTEMPTS = "sms:attempts"  # sms:attempts:{phone}:{scene} → 验证尝试次数

# Lua 脚本：原子验证码校验（检查 + 删除一步完成）
_VERIFY_LUA = """
local code_key = KEYS[1]
local attempts_key = KEYS[2]
local expected_code = ARGV[1]
local max_attempts = tonumber(ARGV[2])

-- 检查尝试次数
local attempts = tonumber(redis.call('GET', attempts_key) or '0')
if attempts >= max_attempts then
    return -1  -- 超过最大尝试次数
end

-- 增加尝试计数
redis.call('INCR', attempts_key)
redis.call('EXPIRE', attempts_key, 3600)

-- 获取并删除验证码（原子操作）
local stored_code = redis.call('GETDEL', code_key)
if stored_code == false then
    return 0  -- 验证码不存在或已使用
end

if stored_code == expected_code then
    -- 验证成功，清除尝试计数
    redis.call('DEL', attempts_key)
    return 1
else
    -- 验证码错误，重新存储验证码（因为 GETDEL 已删除）
    redis.call('SET', code_key, stored_code, 'EX', 300)
    return 0
end
"""


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
    remaining: int
    cooldown_remaining: int


class RedisSmsCodeService:
    """Redis 短信验证码服务

    整合验证码存储、频率限制和短信发送。

    Args:
        sms_client: 阿里云短信客户端
        config: API 配置
    """

    def __init__(
        self,
        sms_client: "AliyunSmsClient",
        config: "APIConfig",
    ) -> None:
        self._sms_client = sms_client
        self._config = config
        self._redis = get_redis()

    # ========== 核心方法 ==========

    def send_code(self, phone: str, scene: str, ip: str | None = None) -> SendCodeResult:
        """发送验证码

        Args:
            phone: 手机号
            scene: 使用场景
            ip: 请求 IP

        Returns:
            发送结果
        """
        # 枚举转字符串
        scene_str = scene.value if hasattr(scene, "value") else str(scene)
        # 1. 检查冷却时间
        cooldown_remaining = self._check_cooldown(phone)
        if cooldown_remaining > 0:
            logger.info(f"手机号 {phone} 冷却中，剩余 {cooldown_remaining} 秒")
            return SendCodeResult(
                success=False,
                error_code="RATE_LIMITED",
                error_message=f"请 {cooldown_remaining} 秒后重试",
                cooldown=cooldown_remaining,
            )

        # 3. 检查每日限制
        remaining = self._check_daily_limit(phone)
        if remaining <= 0:
            logger.warning(f"手机号 {phone} 今日发送次数已达上限")
            return SendCodeResult(
                success=False,
                error_code="DAILY_LIMIT_EXCEEDED",
                error_message="今日发送次数已达上限",
            )

        # 4. 生成验证码
        code = self._generate_code()

        # 5. 发送短信
        template_id = self._sms_client.get_template_id(scene_str)
        send_result = self._sms_client.send_verification_code(phone, code, template_id)

        # 6. 发送成功 → 存储验证码 + 记录频率
        if send_result.success:
            self._store_code(phone, scene_str, code)
            self._record_send(phone)
            logger.info(f"验证码发送成功: {phone}, 场景: {scene_str}")

            # 开发模式：日志输出验证码
            if self._sms_client._is_mock_mode():
                logger.warning(f"[DEV] 验证码: {code} (手机: {phone}, 场景: {scene_str})")
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
        """验证验证码（原子操作）"""
        # 枚举转字符串
        scene_str = scene.value if hasattr(scene, "value") else str(scene)
        code_key = f"{_PREFIX_CODE}:{phone}:{scene_str}"
        attempts_key = f"{_PREFIX_ATTEMPTS}:{phone}:{scene_str}"
        max_attempts = 5

        try:
            if isinstance(self._redis, InMemoryBackend):
                return self._verify_memory(code_key, attempts_key, code, max_attempts)

            # 使用 Lua 脚本原子验证
            result = self._redis.eval(_VERIFY_LUA, 2, code_key, attempts_key, code, max_attempts)

            if result == 1:
                logger.info(f"验证码验证成功: {phone}, 场景: {scene_str}")
                return True
            elif result == -1:
                logger.warning(f"验证码尝试次数超限: {phone}, 场景: {scene_str}")
                return False
            else:
                logger.warning(f"验证码验证失败: {phone}, 场景: {scene_str}")
                return False
        except Exception as e:
            logger.error(f"验证码校验异常: {e}")
            return False

    def _verify_memory(self, code_key: str, attempts_key: str, code: str, max_attempts: int) -> bool:
        """内存后端的验证逻辑"""
        # 检查尝试次数
        attempts = 0
        attempts_val = self._redis.get(attempts_key)
        if attempts_val is not None:
            attempts = int(attempts_val)

        if attempts >= max_attempts:
            logger.warning(f"验证码尝试次数超限 (内存后端)")
            return False

        # 增加尝试计数
        self._redis.incr(attempts_key)

        # 检查验证码
        stored = self._redis.getdel(code_key)
        if stored is None:
            return False

        if stored == code:
            # 成功，清除尝试计数
            self._redis.delete(attempts_key)
            return True
        else:
            # 错误，回写验证码
            self._redis.set(code_key, stored, ex=self._config.SMS_EXPIRE_SECONDS)
            return False

    def check_rate_limit(self, phone: str) -> RateLimitResult:
        """检查发送频率限制"""
        cooldown_remaining = self._check_cooldown(phone)
        if cooldown_remaining > 0:
            return RateLimitResult(can_send=False, remaining=0, cooldown_remaining=cooldown_remaining)

        remaining = self._check_daily_limit(phone)
        if remaining <= 0:
            return RateLimitResult(can_send=False, remaining=0, cooldown_remaining=0)

        return RateLimitResult(can_send=True, remaining=remaining, cooldown_remaining=0)

    # ========== 私有方法 ==========

    def _generate_code(self) -> str:
        code_length = self._config.SMS_CODE_LENGTH
        min_code = 10 ** (code_length - 1)
        max_code = (10**code_length) - 1
        return str(secrets.randbelow(max_code - min_code + 1) + min_code)

    def _store_code(self, phone: str, scene: str, code: str) -> None:
        """存储验证码到 Redis"""
        key = f"{_PREFIX_CODE}:{phone}:{scene}"
        self._redis.set(key, code, ex=self._config.SMS_EXPIRE_SECONDS)

    def _record_send(self, phone: str) -> None:
        """记录发送（冷却 + 每日计数）"""
        # 冷却标记
        cooldown_key = f"{_PREFIX_COOLDOWN}:{phone}"
        self._redis.set(cooldown_key, "1", ex=self._config.SMS_COOLDOWN_SECONDS)

        # 每日计数
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_key = f"{_PREFIX_DAILY}:{phone}:{today}"
        self._redis.incr(daily_key)
        self._redis.expire(daily_key, 86400)

    def _check_cooldown(self, phone: str) -> int:
        """检查冷却剩余秒数"""
        cooldown_key = f"{_PREFIX_COOLDOWN}:{phone}"
        ttl = self._redis.ttl(cooldown_key)
        return max(0, ttl) if ttl > 0 else 0

    def _check_daily_limit(self, phone: str) -> int:
        """检查今日剩余发送次数"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_key = f"{_PREFIX_DAILY}:{phone}:{today}"
        count_val = self._redis.get(daily_key)
        count = int(count_val) if count_val else 0
        return self._config.SMS_DAILY_LIMIT - count
