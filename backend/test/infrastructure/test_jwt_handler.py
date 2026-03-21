"""
JWT Handler 测试
=================

测试 JWT Token 签发和验证功能。
"""

from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError

from src.api.config import APIConfig
from src.infrastructure.jwt_handler import (
    JWTHandler,
    TokenPayload,
    get_jwt_handler,
    init_jwt_handler,
)


class TestTokenPayload:
    """TokenPayload 数据类测试"""

    def test_create_payload(self) -> None:
        """测试创建载荷"""
        now = datetime.now(timezone.utc)
        payload = TokenPayload(
            user_id=123,
            username="test_user",
            role="admin",
            exp=now + timedelta(hours=1),
            iat=now,
        )
        assert payload.user_id == 123
        assert payload.username == "test_user"
        assert payload.role == "admin"


class TestJWTHandler:
    """JWT 处理器测试"""

    @pytest.fixture
    def config(self) -> APIConfig:
        """测试配置"""
        return APIConfig(
            JWT_SECRET_KEY="test-secret-key",
            JWT_ALGORITHM="HS256",
            JWT_EXPIRE_SECONDS=3600,
        )

    @pytest.fixture
    def handler(self, config: APIConfig) -> JWTHandler:
        """JWT 处理器实例"""
        return JWTHandler(config)

    def test_create_token(self, handler: JWTHandler) -> None:
        """测试创建 Token"""
        token = handler.create_token(
            user_id=123,
            username="test_user",
            role="admin",
        )
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT 格式：header.payload.signature
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_token_without_username(self, handler: JWTHandler) -> None:
        """测试创建无用户名的 Token"""
        token = handler.create_token(
            user_id=456,
            username=None,
            role="user",
        )
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    def test_verify_token_success(self, handler: JWTHandler) -> None:
        """测试验证有效 Token"""
        token = handler.create_token(
            user_id=123,
            username="test_user",
            role="admin",
        )
        payload = handler.verify_token(token)
        assert payload.user_id == 123
        assert payload.username == "test_user"
        assert payload.role == "admin"
        assert isinstance(payload.exp, datetime)
        assert isinstance(payload.iat, datetime)

    def test_verify_token_expired(self, handler: JWTHandler) -> None:
        """测试验证过期 Token"""
        # 手动创建一个已过期的 token
        from jose import jwt as jose_jwt

        now = datetime.now(timezone.utc)
        expired_payload = {
            "user_id": 123,
            "username": "test_user",
            "role": "admin",
            "iat": now,
            "exp": now - timedelta(seconds=1),  # 已过期
        }
        expired_token = jose_jwt.encode(
            expired_payload,
            "test-secret-key",
            algorithm="HS256",
        )

        with pytest.raises(JWTError, match="过期|expired"):
            handler.verify_token(expired_token)

    def test_verify_token_invalid(self, handler: JWTHandler) -> None:
        """测试验证无效 Token"""
        with pytest.raises(JWTError):
            handler.verify_token("invalid.token.string")

    def test_verify_token_tampered(self, handler: JWTHandler) -> None:
        """测试验证被篡改的 Token"""
        token = handler.create_token(
            user_id=123,
            username="test_user",
            role="admin",
        )
        # 篡改 token
        tampered_token = token[:-10] + "tampered"
        with pytest.raises(JWTError):
            handler.verify_token(tampered_token)

    def test_decode_token(self, handler: JWTHandler) -> None:
        """测试解码 Token（不验证）"""
        token = handler.create_token(
            user_id=123,
            username="test_user",
            role="admin",
        )
        decoded = handler.decode_token(token)
        assert decoded["user_id"] == 123
        assert decoded["username"] == "test_user"
        assert decoded["role"] == "admin"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_decode_invalid_token(self, handler: JWTHandler) -> None:
        """测试解码无效 Token"""
        with pytest.raises(JWTError):
            handler.decode_token("invalid.token")

    def test_get_expired_at(self, handler: JWTHandler) -> None:
        """测试获取过期时间"""
        token = handler.create_token(
            user_id=123,
            username="test_user",
            role="admin",
        )
        expired_at = handler.get_expired_at(token)
        now = datetime.now(timezone.utc)
        # 过期时间应该在未来约 3600 秒内（1小时，基于测试配置）
        time_diff = expired_at - now
        assert timedelta(seconds=3500) <= time_diff <= timedelta(seconds=3700)

    def test_get_expired_at_invalid_token(self, handler: JWTHandler) -> None:
        """测试获取无效 Token 的过期时间"""
        with pytest.raises(JWTError):
            handler.get_expired_at("invalid.token")

    def test_different_secret_keys(self, config: APIConfig) -> None:
        """测试不同密钥生成的 Token 不可互相验证"""
        handler1 = JWTHandler(config)
        config2 = APIConfig(
            JWT_SECRET_KEY="different-secret-key",
            JWT_ALGORITHM="HS256",
            JWT_EXPIRE_SECONDS=3600,
        )
        handler2 = JWTHandler(config2)

        token1 = handler1.create_token(user_id=123, username="user1", role="user")
        # 使用不同密钥验证应失败
        with pytest.raises(JWTError):
            handler2.verify_token(token1)


class TestGlobalJWTHandler:
    """全局 JWT 处理器测试"""

    def test_init_jwt_handler(self) -> None:
        """测试初始化全局 JWT 处理器"""
        config = APIConfig(
            JWT_SECRET_KEY="test-secret",
            JWT_ALGORITHM="HS256",
            JWT_EXPIRE_SECONDS=3600,
        )
        handler = init_jwt_handler(config)
        assert isinstance(handler, JWTHandler)
        assert get_jwt_handler() is handler

    def test_get_jwt_handler_before_init(self) -> None:
        """测试在初始化前获取处理器"""
        # 重置全局变量
        import src.infrastructure.jwt_handler as jwt_module
        jwt_module.jwt_handler = None
        with pytest.raises(ValueError, match="JWT 处理器未初始化"):
            get_jwt_handler()
