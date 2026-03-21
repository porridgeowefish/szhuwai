"""
JWT Handler Module
==================

提供 JWT Token 签发和验证功能。
"""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from jose import JWTError, jwt
from pydantic import BaseModel

if TYPE_CHECKING:
    from src.api.config import APIConfig


class TokenPayload(BaseModel):
    """Token 载荷数据"""

    user_id: int
    username: str | None
    role: str
    exp: datetime
    iat: datetime


class JWTHandler:
    """JWT Token 处理器"""

    def __init__(self, config: "APIConfig") -> None:
        """初始化 JWT 处理器

        Args:
            config: API 配置对象
        """
        self._secret_key = config.JWT_SECRET_KEY
        self._algorithm = config.JWT_ALGORITHM
        self._expire_seconds = config.JWT_EXPIRE_SECONDS

    def create_token(
        self,
        user_id: int,
        username: str | None,
        role: str = "user",
    ) -> str:
        """签发 JWT Token

        Args:
            user_id: 用户 ID
            username: 用户名
            role: 用户角色

        Returns:
            JWT Token 字符串

        Raises:
            ValueError: 当参数无效时
        """
        if user_id <= 0:
            raise ValueError("user_id 必须为正整数")

        now = datetime.now(timezone.utc)
        expire_at = now + timedelta(seconds=self._expire_seconds)

        payload = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "iat": now,
            "exp": expire_at,
        }

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_token(self, token: str) -> TokenPayload:
        """验证 JWT Token，返回载荷

        Args:
            token: JWT Token 字符串

        Returns:
            TokenPayload 对象

        Raises:
            JWTError: 当 Token 无效、过期或签名错误时
        """
        try:
            decoded = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except JWTError as e:
            raise JWTError(f"Token 验证失败: {e}") from e

        # 检查过期时间
        exp = decoded.get("exp")
        if exp is None:
            raise JWTError("Token 缺少过期时间")

        exp_datetime = datetime.fromtimestamp(exp, timezone.utc)
        now = datetime.now(timezone.utc)

        if exp_datetime < now:
            raise JWTError("Token 已过期")

        return TokenPayload(
            user_id=decoded.get("user_id", 0),
            username=decoded.get("username"),
            role=decoded.get("role", "user"),
            exp=exp_datetime,
            iat=datetime.fromtimestamp(
                decoded.get("iat", 0),
                timezone.utc,
            ),
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        """解码 JWT Token（不验证签名）

        Args:
            token: JWT Token 字符串

        Returns:
            解码后的字典

        Raises:
            JWTError: 当 Token 格式错误时
        """
        try:
            # 不验证签名时仍需提供 key，使用空字符串
            return jwt.decode(
                token,
                "",
                options={"verify_signature": False},
            )
        except JWTError as e:
            raise JWTError(f"Token 解码失败: {e}") from e

    def get_expired_at(self, token: str) -> datetime:
        """获取 Token 过期时间

        Args:
            token: JWT Token 字符串

        Returns:
            过期时间（UTC 时区）

        Raises:
            JWTError: 当 Token 格式错误时
        """
        decoded = self.decode_token(token)
        exp = decoded.get("exp")
        if exp is None:
            raise JWTError("Token 缺少过期时间")

        return datetime.fromtimestamp(exp, timezone.utc)


# 全局实例
jwt_handler: JWTHandler | None = None


def get_jwt_handler() -> JWTHandler:
    """获取全局 JWT 处理器实例

    Returns:
        JWTHandler 实例

    Raises:
        ValueError: 当处理器未初始化时
    """
    if jwt_handler is None:
        raise ValueError("JWT 处理器未初始化，请先调用 init_jwt_handler()")
    return jwt_handler


def init_jwt_handler(config: "APIConfig") -> JWTHandler:
    """初始化全局 JWT 处理器

    Args:
        config: API 配置对象

    Returns:
        初始化的 JWTHandler 实例
    """
    global jwt_handler
    jwt_handler = JWTHandler(config)
    return jwt_handler
