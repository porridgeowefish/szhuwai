"""
Password Hasher Module
======================

提供密码加密和验证功能，使用 bcrypt 算法。
"""

import re


class PasswordHasher:
    """密码加密工具类

    使用 bcrypt 算法进行密码加密，提供安全的密码存储方案。

    特点：
    - 自动生成和管理 salt
    - 自适应哈希（可调整工作因子）
    - 内置时间复杂度防护
    """

    # bcrypt 工作因子（越高越安全，但越慢）
    # 推荐值：12（约 300ms），4-31 范围内，2 的幂次
    ROUNDS: int = 12

    # bcrypt 哈希正则表达式
    _BCRYPT_PATTERN = re.compile(
        r"^\$2[aby]\$(\d+)\$[./A-Za-z0-9]{53}$"
    )

    def hash_password(self, password: str) -> str:
        """加密密码

        Args:
            password: 明文密码

        Returns:
            加密后的密码哈希（包含 salt）

        Raises:
            ValueError: 当密码为 None 时
        """
        if password is None:
            raise ValueError("密码不能为 None")

        # 导入 bcrypt（延迟导入，避免模块级导入问题）
        try:
            import bcrypt
        except ImportError as e:
            raise ImportError(
                "bcrypt 模块未安装，请运行: pip install bcrypt"
            ) from e

        # 将密码编码为 bytes
        password_bytes = password.encode("utf-8")

        # 生成哈希：salt 由 bcrypt 自动生成
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=self.ROUNDS))

        # 返回字符串格式
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码

        Args:
            password: 明文密码
            hashed: 存储的密码哈希

        Returns:
            密码是否匹配
        """
        # 防御性编程：处理无效输入
        if password is None or hashed is None:
            return False

        # 检查哈希格式
        if not self._BCRYPT_PATTERN.match(hashed):
            return False

        try:
            import bcrypt
        except ImportError:
            return False

        try:
            # 将密码和哈希编码为 bytes
            password_bytes = password.encode("utf-8")
            hashed_bytes = hashed.encode("utf-8")

            # 验证密码
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            # 任何异常都视为验证失败
            return False

    def needs_rehash(self, hashed: str) -> bool:
        """检查是否需要重新哈希

        当工作因子改变时，旧的哈希可能需要更新。

        Args:
            hashed: 存储的密码哈希

        Returns:
            是否需要重新哈希
        """
        # 检查哈希格式
        match = self._BCRYPT_PATTERN.match(hashed)
        if not match:
            # 无效格式，需要重新哈希
            return True

        # 提取工作因子
        rounds = int(match.group(1))

        # 如果工作因子小于当前值，需要重新哈希
        return rounds < self.ROUNDS


# 全局实例
password_hasher: PasswordHasher = PasswordHasher()


def get_password_hasher() -> PasswordHasher:
    """获取全局密码加密器实例

    Returns:
        PasswordHasher 实例（单例）
    """
    return password_hasher
