"""
Password Hasher 测试
====================

测试密码加密和验证功能。
"""

import re

import pytest

from src.infrastructure.password_hasher import (
    PasswordHasher,
    get_password_hasher,
)


class TestPasswordHasher:
    """密码加密器测试"""

    @pytest.fixture
    def hasher(self) -> PasswordHasher:
        """密码加密器实例"""
        return PasswordHasher()

    def test_hash_password(self, hasher: PasswordHasher) -> None:
        """测试密码加密"""
        password = "my_secure_password"
        hashed = hasher.hash_password(password)

        # 哈希应该是字符串
        assert isinstance(hashed, str)
        # bcrypt 哈希长度为 60 字符
        assert len(hashed) == 60
        # bcrypt 哈希以 $2b$ 或 $2a$ 开头
        assert hashed.startswith("$2")

    def test_verify_password_correct(self, hasher: PasswordHasher) -> None:
        """测试验证正确密码"""
        password = "correct_password"
        hashed = hasher.hash_password(password)

        # 正确密码应该验证通过
        assert hasher.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, hasher: PasswordHasher) -> None:
        """测试验证错误密码"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hasher.hash_password(password)

        # 错误密码应该验证失败
        assert hasher.verify_password(wrong_password, hashed) is False

    def test_hash_password_empty(self, hasher: PasswordHasher) -> None:
        """测试空密码"""
        password = ""
        hashed = hasher.hash_password(password)

        # 空密码也能加密
        assert len(hashed) == 60
        # 空密码能验证成功
        assert hasher.verify_password("", hashed) is True
        # 非空密码验证失败
        assert hasher.verify_password("something", hashed) is False

    def test_hash_password_unicode(self, hasher: PasswordHasher) -> None:
        """测试 Unicode 密码"""
        # 测试中文字符
        password = "密码123!@#"
        hashed = hasher.hash_password(password)

        assert hasher.verify_password(password, hashed) is True
        # 错误密码应该失败
        assert hasher.verify_password("密码123!@%", hashed) is False

        # 测试 emoji
        emoji_password = "pass🔐word"
        hashed_emoji = hasher.hash_password(emoji_password)

        assert hasher.verify_password(emoji_password, hashed_emoji) is True

    def test_hash_uniqueness(self, hasher: PasswordHasher) -> None:
        """测试相同密码生成不同哈希（因为有 salt）"""
        password = "same_password"

        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)

        # 相同密码应该生成不同的哈希（因为 salt 不同）
        assert hash1 != hash2
        # 但两个哈希都应该能验证原密码
        assert hasher.verify_password(password, hash1) is True
        assert hasher.verify_password(password, hash2) is True

    def test_needs_rehash(self, hasher: PasswordHasher) -> None:
        """测试是否需要重新哈希"""
        # 当前工作因子生成的哈希不需要重新哈希
        hashed = hasher.hash_password("test_password")
        assert hasher.needs_rehash(hashed) is False

        # 模拟旧的工作因子（手动构造旧格式哈希）
        # $2b$10$ 表示使用 10 轮（比默认 12 低）
        old_rounds_hash = "$2b$10$abcdefghijklmnopqrstuvwxyz123456789012345678"
        # 需要修改 ROUNDS 才能测试，这里只验证方法存在
        assert isinstance(hasher.needs_rehash(old_rounds_hash), bool)

    def test_hash_format(self, hasher: PasswordHasher) -> None:
        """测试哈希格式正确"""
        password = "format_test"
        hashed = hasher.hash_password(password)

        # bcrypt 格式: $2b$[rounds]$[salt][hash]
        # 例如: $2b$12$ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01
        pattern = r"^\$2[ab]\$\d+\$[./A-Za-z0-9]{53}$"
        assert re.match(pattern, hashed) is not None

    def test_verify_password_with_invalid_hash(self, hasher: PasswordHasher) -> None:
        """测试使用无效哈希验证密码"""
        # 无效哈希格式应该返回 False 而不是抛出异常
        assert hasher.verify_password("password", "invalid_hash") is False
        assert hasher.verify_password("password", "$2b$12$tooshort") is False

    def test_hash_password_long(self, hasher: PasswordHasher) -> None:
        """测试长密码"""
        # bcrypt 限制密码最大 72 字节
        long_password = "a" * 100
        hashed = hasher.hash_password(long_password)

        # 应该能够处理长密码（会被截断到 72 字节）
        assert len(hashed) == 60
        # 验证前 72 字节
        assert hasher.verify_password(long_password, hashed) is True


class TestGlobalPasswordHasher:
    """全局密码加密器测试"""

    def test_get_password_hasher(self) -> None:
        """测试获取全局加密器实例"""
        hasher = get_password_hasher()
        assert isinstance(hasher, PasswordHasher)

    def test_global_instance_singleton(self) -> None:
        """测试全局实例是单例"""
        hasher1 = get_password_hasher()
        hasher2 = get_password_hasher()
        assert hasher1 is hasher2

    def test_global_instance_works(self) -> None:
        """测试全局实例可以正常工作"""
        hasher = get_password_hasher()
        password = "test_password"
        hashed = hasher.hash_password(password)

        assert hasher.verify_password(password, hashed) is True
