"""
认证服务
========

提供用户注册、登录、密码管理、手机号绑定等认证功能。
"""

from dataclasses import dataclass
from typing import Any

from loguru import logger
from src.repositories.user_repo import UserRepository
from src.schemas.user import UserCreate, UserResponse


@dataclass
class LoginResult:
    """登录结果"""

    success: bool
    user: UserResponse | None = None
    token: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class AuthService:
    """认证服务

    整合用户仓库、短信服务、JWT 处理器和密码加密器，
    提供完整的认证功能。

    Args:
        user_repo: 用户仓库
        sms_service: 短信服务
        jwt_handler: JWT 处理器
        password_hasher: 密码加密器
    """

    def __init__(
        self,
        user_repo: UserRepository,
        sms_service: Any,  # SmsService (避免循环导入)
        jwt_handler: Any,  # JWTHandler
        password_hasher: Any,  # PasswordHasher
    ) -> None:
        """初始化认证服务

        Args:
            user_repo: 用户仓库
            sms_service: 短信服务
            jwt_handler: JWT 处理器
            password_hasher: 密码加密器
        """
        self._user_repo = user_repo
        self._sms_service = sms_service
        self._jwt_handler = jwt_handler
        self._password_hasher = password_hasher

    # ===== 注册 =====

    def register_by_username(self, username: str, password: str) -> tuple[UserResponse, str] | None:
        """用户名注册

        Args:
            username: 用户名
            password: 密码

        Returns:
            (用户信息, token) 或 None（用户名已存在）
        """
        # 1. 检查用户名是否存在
        if self._user_repo.exists_by_username(username):
            logger.info(f"用户名注册失败: {username} 已存在")
            return None

        # 2. 加密密码
        password_hash = self._password_hasher.hash_password(password)

        # 3. 创建用户
        user = self._user_repo.create(
            UserCreate(username=username, phone=None, password=None, role="user", status="active"),
            password_hash=password_hash,
        )

        # 4. 签发 Token
        token = self._jwt_handler.create_token(user.id, user.username, user.role)

        logger.info(f"用户名注册成功: {user.id}")
        return (UserResponse.model_validate(user), token)

    def register_by_phone(
        self,
        phone: str,
        code: str,
        password: str | None = None,
        username: str | None = None,
    ) -> tuple[UserResponse, str] | None:
        """手机号注册

        Args:
            phone: 手机号
            code: 验证码
            password: 密码（可选）
            username: 用户名（可选）

        Returns:
            (用户信息, token) 或 None（注册失败）
        """
        # 1. 验证验证码
        if not self._sms_service.verify_code(phone, code, "register"):
            logger.warning(f"手机号注册失败: {phone} 验证码错误")
            return None

        # 2. 检查手机号是否已被注册
        if self._user_repo.exists_by_phone(phone):
            logger.info(f"手机号注册失败: {phone} 已存在")
            return None

        # 3. 如果提供了用户名，检查用户名是否已存在
        if username and self._user_repo.exists_by_username(username):
            logger.info(f"手机号注册失败: 用户名 {username} 已存在")
            return None

        # 4. 加密密码（如果提供了密码）
        password_hash = None
        if password:
            password_hash = self._password_hasher.hash_password(password)

        # 5. 创建用户
        user = self._user_repo.create(
            UserCreate(
                phone=phone,
                username=username,
                password=password,
                role="user",
                status="active",
            ),
            password_hash=password_hash,
        )

        # 6. 签发 Token
        token = self._jwt_handler.create_token(user.id, user.username, user.role)

        logger.info(f"手机号注册成功: {user.id}, 手机: {phone}")
        return (UserResponse.model_validate(user), token)

    # ===== 登录 =====

    def login_by_username(self, username: str, password: str) -> LoginResult:
        """用户名登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            登录结果
        """
        # 1. 查找用户
        user = self._user_repo.get_by_username(username)
        if not user:
            logger.info(f"用户名登录失败: {username} 不存在")
            return LoginResult(success=False, error_code="USER_NOT_FOUND", error_message="用户不存在")

        # 2. 验证密码
        if not user.password_hash:
            logger.warning(f"用户名登录失败: {username} 未设置密码")
            return LoginResult(success=False, error_code="INVALID_PASSWORD", error_message="密码错误")

        if not self._password_hasher.verify_password(password, user.password_hash):
            logger.warning(f"用户名登录失败: {username} 密码错误")
            return LoginResult(success=False, error_code="INVALID_PASSWORD", error_message="密码错误")

        # 3. 检查状态
        if user.status != "active":
            logger.warning(f"用户名登录失败: {username} 账号已被禁用")
            return LoginResult(success=False, error_code="ACCOUNT_DISABLED", error_message="账号已被禁用")

        # 4. 更新登录时间
        self._user_repo.update_last_login(user.id)

        # 5. 签发 Token
        token = self._jwt_handler.create_token(user.id, user.username, user.role)

        logger.info(f"用户名登录成功: {user.id}")
        return LoginResult(
            success=True,
            user=UserResponse.model_validate(user),
            token=token,
        )

    def login_by_phone(self, phone: str, code: str) -> LoginResult:
        """手机号登录

        Args:
            phone: 手机号
            code: 验证码

        Returns:
            登录结果
        """
        # 1. 验证验证码
        if not self._sms_service.verify_code(phone, code, "login"):
            logger.warning(f"手机号登录失败: {phone} 验证码错误")
            return LoginResult(success=False, error_code="INVALID_CODE", error_message="验证码错误")

        # 2. 查找用户
        user = self._user_repo.get_by_phone(phone)
        if not user:
            logger.info(f"手机号登录失败: {phone} 未注册")
            return LoginResult(success=False, error_code="PHONE_NOT_REGISTERED", error_message="手机号未注册")

        # 3. 检查状态
        if user.status != "active":
            logger.warning(f"手机号登录失败: {phone} 账号已被禁用")
            return LoginResult(success=False, error_code="ACCOUNT_DISABLED", error_message="账号已被禁用")

        # 4. 更新登录时间
        self._user_repo.update_last_login(user.id)

        # 5. 签发 Token
        token = self._jwt_handler.create_token(user.id, user.username, user.role)

        logger.info(f"手机号登录成功: {user.id}")
        return LoginResult(
            success=True,
            user=UserResponse.model_validate(user),
            token=token,
        )

    # ===== 密码管理 =====

    def reset_password(self, phone: str, code: str, new_password: str) -> bool:
        """重置密码

        Args:
            phone: 手机号
            code: 验证码
            new_password: 新密码

        Returns:
            是否成功
        """
        # 1. 验证验证码
        if not self._sms_service.verify_code(phone, code, "reset_password"):
            logger.warning(f"重置密码失败: {phone} 验证码错误")
            return False

        # 2. 查找用户
        user = self._user_repo.get_by_phone(phone)
        if not user:
            logger.warning(f"重置密码失败: {phone} 用户不存在")
            return False

        # 3. 加密新密码
        password_hash = self._password_hasher.hash_password(new_password)

        # 4. 更新密码
        self._user_repo.update_password(user.id, password_hash)

        logger.info(f"重置密码成功: {user.id}")
        return True

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码

        Args:
            user_id: 用户 ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            是否成功
        """
        # 1. 获取用户
        user = self._user_repo.get_by_id(user_id)
        if not user:
            logger.warning(f"修改密码失败: {user_id} 用户不存在")
            return False

        # 2. 验证旧密码
        if not user.password_hash:
            logger.warning(f"修改密码失败: {user_id} 未设置密码")
            return False

        if not self._password_hasher.verify_password(old_password, user.password_hash):
            logger.warning(f"修改密码失败: {user_id} 旧密码错误")
            return False

        # 3. 加密新密码
        password_hash = self._password_hasher.hash_password(new_password)

        # 4. 更新密码
        self._user_repo.update_password(user_id, password_hash)

        logger.info(f"修改密码成功: {user_id}")
        return True

    # ===== 手机管理 =====

    def bind_phone(self, user_id: int, phone: str, code: str) -> UserResponse | None:
        """绑定手机

        Args:
            user_id: 用户 ID
            phone: 手机号
            code: 验证码

        Returns:
            更新后的用户信息，失败返回 None
        """
        # 1. 验证验证码
        if not self._sms_service.verify_code(phone, code, "bind"):
            logger.warning(f"绑定手机失败: {phone} 验证码错误")
            return None

        # 2. 检查手机号是否已被其他用户绑定
        if self._user_repo.exists_by_phone(phone):
            logger.info(f"绑定手机失败: {phone} 已被其他用户绑定")
            return None

        # 3. 绑定手机号
        success = self._user_repo.bind_phone(user_id, phone)
        if not success:
            logger.warning(f"绑定手机失败: {user_id} 用户不存在")
            return None

        # 4. 返回更新后的用户信息
        user = self._user_repo.get_by_id(user_id)
        if user:
            logger.info(f"绑定手机成功: {user_id} -> {phone}")
            return UserResponse.model_validate(user)

        return None

    def unbind_phone(self, user_id: int, code: str) -> UserResponse | None:
        """解绑手机

        Args:
            user_id: 用户 ID
            code: 验证码（验证原手机号）

        Returns:
            更新后的用户信息，失败返回 None
        """
        # 1. 获取用户
        user = self._user_repo.get_by_id(user_id)
        if not user:
            logger.warning(f"解绑手机失败: {user_id} 用户不存在")
            return None

        # 2. 检查是否绑定了手机号
        if not user.phone:
            logger.warning(f"解绑手机失败: {user_id} 未绑定手机号")
            return None

        # 3. 验证验证码（验证原手机号）
        if not self._sms_service.verify_code(user.phone, code, "unbind"):
            logger.warning(f"解绑手机失败: {user.phone} 验证码错误")
            return None

        # 4. 解绑手机号
        updated_user = self._user_repo.update(user_id, phone=None)
        if updated_user:
            logger.info(f"解绑手机成功: {user_id}")
            return UserResponse.model_validate(updated_user)

        return None

    # ===== 辅助方法 =====

    def get_user_by_id(self, user_id: int) -> UserResponse | None:
        """根据 ID 获取用户

        Args:
            user_id: 用户 ID

        Returns:
            用户信息，不存在返回 None
        """
        user = self._user_repo.get_by_id(user_id)
        if user:
            return UserResponse.model_validate(user)
        return None

    def validate_token(self, token: str) -> dict[str, Any] | None:
        """验证 Token

        Args:
            token: JWT Token

        Returns:
            Token 载荷字典，验证失败返回 None
        """
        try:
            payload = self._jwt_handler.verify_token(token)
            return {
                "user_id": payload.user_id,
                "username": payload.username,
                "role": payload.role,
                "exp": payload.exp,
            }
        except Exception as e:
            logger.warning(f"Token 验证失败: {e}")
            return None
