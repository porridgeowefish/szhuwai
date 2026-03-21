"""
AuthService 单元测试
====================
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.services.auth_service import AuthService, LoginResult
from src.schemas.user import UserResponse


class TestAuthService:
    """认证服务测试"""

    @pytest.fixture
    def mock_user_repo(self) -> MagicMock:
        """创建模拟用户仓库"""
        repo = MagicMock()
        return repo

    @pytest.fixture
    def mock_sms_service(self) -> MagicMock:
        """创建模拟短信服务"""
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_jwt_handler(self) -> MagicMock:
        """创建模拟 JWT 处理器"""
        handler = MagicMock()
        handler.create_token.return_value = "test_token"
        return handler

    @pytest.fixture
    def mock_password_hasher(self) -> MagicMock:
        """创建模拟密码加密器"""
        hasher = MagicMock()
        hasher.hash_password.return_value = "hashed_password"
        hasher.verify_password.return_value = True
        return hasher

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """创建模拟用户"""
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        user.phone = "13800138000"
        user.password_hash = "hashed_password"
        user.role = "user"
        user.status = "active"
        user.created_at = datetime.now()
        user.updated_at = datetime.now()
        user.last_login_at = None
        return user

    @pytest.fixture
    def auth_service(
        self,
        mock_user_repo: MagicMock,
        mock_sms_service: MagicMock,
        mock_jwt_handler: MagicMock,
        mock_password_hasher: MagicMock,
    ) -> AuthService:
        """创建 AuthService 实例"""
        return AuthService(mock_user_repo, mock_sms_service, mock_jwt_handler, mock_password_hasher)

    # ===== 用户名注册测试 =====

    def test_register_by_username_success(
        self, auth_service: AuthService, mock_user_repo: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试用户名注册成功"""
        # 模拟用户名不存在
        mock_user_repo.exists_by_username.return_value = False
        mock_user_repo.create.return_value = mock_user

        result = auth_service.register_by_username("testuser", "password123")

        assert result is not None
        user_response, token = result
        assert isinstance(user_response, UserResponse)
        assert user_response.id == 1
        assert user_response.username == "testuser"
        assert token == "test_token"

        # 验证调用
        mock_user_repo.exists_by_username.assert_called_once_with("testuser")
        mock_password_hasher = auth_service._password_hasher
        mock_password_hasher.hash_password.assert_called_once_with("password123")
        mock_user_repo.create.assert_called_once()
        mock_jwt_handler = auth_service._jwt_handler
        mock_jwt_handler.create_token.assert_called_once_with(1, "testuser", "user")

    def test_register_by_username_duplicate(self, auth_service: AuthService, mock_user_repo: MagicMock) -> None:
        """测试用户名已存在"""
        # 模拟用户名已存在
        mock_user_repo.exists_by_username.return_value = True

        result = auth_service.register_by_username("testuser", "password123")

        assert result is None
        mock_user_repo.exists_by_username.assert_called_once_with("testuser")
        mock_user_repo.create.assert_not_called()

    # ===== 手机号注册测试 =====

    def test_register_by_phone_with_password(
        self, auth_service: AuthService, mock_user_repo: MagicMock, mock_sms_service: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试手机号注册成功（带密码）"""
        # 模拟验证码验证成功，手机号不存在
        mock_sms_service.verify_code.return_value = True
        mock_user_repo.exists_by_phone.return_value = False
        mock_user_repo.exists_by_username.return_value = False
        mock_user_repo.create.return_value = mock_user

        result = auth_service.register_by_phone("13800138000", "123456", "password123", "newuser")

        assert result is not None
        user_response, token = result
        assert isinstance(user_response, UserResponse)

        # 验证调用
        mock_sms_service.verify_code.assert_called_once_with("13800138000", "123456", "register")
        mock_user_repo.exists_by_phone.assert_called_once_with("13800138000")
        mock_user_repo.create.assert_called_once()

    def test_register_by_phone_invalid_code(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock
    ) -> None:
        """测试手机号注册验证码错误"""
        # 模拟验证码验证失败
        mock_sms_service.verify_code.return_value = False

        result = auth_service.register_by_phone("13800138000", "wrong_code", "password123")

        assert result is None
        mock_sms_service.verify_code.assert_called_once()
        mock_user_repo.create.assert_not_called()

    def test_register_by_phone_already_exists(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock
    ) -> None:
        """测试手机号已存在"""
        # 模拟验证码验证成功，但手机号已存在
        mock_sms_service.verify_code.return_value = True
        mock_user_repo.exists_by_phone.return_value = True

        result = auth_service.register_by_phone("13800138000", "123456", "password123")

        assert result is None
        mock_user_repo.create.assert_not_called()

    def test_register_by_phone_without_password(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试手机号注册成功（无密码）"""
        # 模拟验证码验证成功，手机号不存在
        mock_sms_service.verify_code.return_value = True
        mock_user_repo.exists_by_phone.return_value = False
        mock_user_repo.exists_by_username.return_value = False
        mock_user_repo.create.return_value = mock_user

        result = auth_service.register_by_phone("13800138000", "123456")

        assert result is not None
        mock_user_repo.create.assert_called_once()

    # ===== 用户名登录测试 =====

    def test_login_by_username_success(
        self, auth_service: AuthService, mock_user_repo: MagicMock, mock_password_hasher: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试用户名登录成功"""
        # 模拟用户存在，密码验证成功
        mock_user_repo.get_by_username.return_value = mock_user
        mock_password_hasher.verify_password.return_value = True

        result = auth_service.login_by_username("testuser", "password123")

        assert isinstance(result, LoginResult)
        assert result.success is True
        assert result.user is not None
        assert result.user.id == 1
        assert result.token == "test_token"
        assert result.error_code is None
        assert result.error_message is None

        # 验证调用
        mock_user_repo.get_by_username.assert_called_once_with("testuser")
        mock_password_hasher.verify_password.assert_called_once_with("password123", "hashed_password")
        mock_user_repo.update_last_login.assert_called_once_with(1)
        mock_jwt_handler = auth_service._jwt_handler
        mock_jwt_handler.create_token.assert_called_once()

    def test_login_by_username_user_not_found(self, auth_service: AuthService, mock_user_repo: MagicMock) -> None:
        """测试用户名登录用户不存在"""
        # 模拟用户不存在
        mock_user_repo.get_by_username.return_value = None

        result = auth_service.login_by_username("nonexistent", "password123")

        assert isinstance(result, LoginResult)
        assert result.success is False
        assert result.error_code == "USER_NOT_FOUND"
        assert result.error_message == "用户不存在"
        assert result.user is None
        assert result.token is None

    def test_login_by_username_wrong_password(
        self, auth_service: AuthService, mock_user_repo: MagicMock, mock_password_hasher: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试用户名登录密码错误"""
        # 模拟用户存在，密码验证失败
        mock_user_repo.get_by_username.return_value = mock_user
        mock_password_hasher.verify_password.return_value = False

        result = auth_service.login_by_username("testuser", "wrong_password")

        assert isinstance(result, LoginResult)
        assert result.success is False
        assert result.error_code == "INVALID_PASSWORD"
        assert result.error_message == "密码错误"

    def test_login_by_username_account_disabled(
        self, auth_service: AuthService, mock_user_repo: MagicMock, mock_password_hasher: MagicMock
    ) -> None:
        """测试用户名登录账号已被禁用"""
        # 模拟用户存在但已禁用
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.password_hash = "hashed_password"
        mock_user.status = "disabled"

        mock_user_repo.get_by_username.return_value = mock_user
        mock_password_hasher.verify_password.return_value = True

        result = auth_service.login_by_username("testuser", "password123")

        assert isinstance(result, LoginResult)
        assert result.success is False
        assert result.error_code == "ACCOUNT_DISABLED"
        assert result.error_message == "账号已被禁用"

    # ===== 手机号登录测试 =====

    def test_login_by_phone_success(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试手机号登录成功"""
        # 模拟验证码验证成功，用户存在
        mock_sms_service.verify_code.return_value = True
        mock_user_repo.get_by_phone.return_value = mock_user

        result = auth_service.login_by_phone("13800138000", "123456")

        assert isinstance(result, LoginResult)
        assert result.success is True
        assert result.user is not None
        assert result.token == "test_token"

        # 验证调用
        mock_sms_service.verify_code.assert_called_once_with("13800138000", "123456", "login")
        mock_user_repo.get_by_phone.assert_called_once_with("13800138000")

    def test_login_by_phone_invalid_code(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock
    ) -> None:
        """测试手机号登录验证码错误"""
        # 模拟验证码验证失败
        mock_sms_service.verify_code.return_value = False

        result = auth_service.login_by_phone("13800138000", "wrong_code")

        assert isinstance(result, LoginResult)
        assert result.success is False
        assert result.error_code == "INVALID_CODE"
        assert result.error_message == "验证码错误"

        mock_user_repo.get_by_phone.assert_not_called()

    def test_login_by_phone_not_registered(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock
    ) -> None:
        """测试手机号登录手机号未注册"""
        # 模拟验证码验证成功，但用户不存在
        mock_sms_service.verify_code.return_value = True
        mock_user_repo.get_by_phone.return_value = None

        result = auth_service.login_by_phone("13800138000", "123456")

        assert isinstance(result, LoginResult)
        assert result.success is False
        assert result.error_code == "PHONE_NOT_REGISTERED"
        assert result.error_message == "手机号未注册"

    # ===== 密码管理测试 =====

    def test_reset_password_success(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试重置密码成功"""
        # 模拟验证码验证成功，用户存在
        mock_sms_service.verify_code.return_value = True
        mock_user_repo.get_by_phone.return_value = mock_user

        result = auth_service.reset_password("13800138000", "123456", "new_password")

        assert result is True
        mock_user_repo.update_password.assert_called_once_with(1, "hashed_password")

    def test_reset_password_invalid_code(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock
    ) -> None:
        """测试重置密码验证码错误"""
        # 模拟验证码验证失败
        mock_sms_service.verify_code.return_value = False

        result = auth_service.reset_password("13800138000", "wrong_code", "new_password")

        assert result is False
        mock_user_repo.update_password.assert_not_called()

    def test_change_password_success(
        self, auth_service: AuthService, mock_user_repo: MagicMock, mock_password_hasher: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试修改密码成功"""
        # 模拟用户存在，旧密码验证成功
        mock_user_repo.get_by_id.return_value = mock_user
        mock_password_hasher.verify_password.return_value = True

        result = auth_service.change_password(1, "old_password", "new_password")

        assert result is True
        mock_password_hasher.verify_password.assert_called_once_with("old_password", "hashed_password")
        mock_user_repo.update_password.assert_called_once_with(1, "hashed_password")

    def test_change_password_wrong_old_password(
        self, auth_service: AuthService, mock_user_repo: MagicMock, mock_password_hasher: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试修改密码旧密码错误"""
        # 模拟用户存在，旧密码验证失败
        mock_user_repo.get_by_id.return_value = mock_user
        mock_password_hasher.verify_password.return_value = False

        result = auth_service.change_password(1, "wrong_old_password", "new_password")

        assert result is False
        mock_user_repo.update_password.assert_not_called()

    # ===== 手机管理测试 =====

    def test_bind_phone_success(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试绑定手机成功"""
        # 模拟验证码验证成功，手机号未被其他用户绑定
        mock_sms_service.verify_code.return_value = True
        mock_user_repo.exists_by_phone.return_value = False
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.bind_phone.return_value = True

        result = auth_service.bind_phone(1, "13800138000", "123456")

        assert result is not None
        assert isinstance(result, UserResponse)
        mock_user_repo.bind_phone.assert_called_once_with(1, "13800138000")

    def test_bind_phone_invalid_code(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock
    ) -> None:
        """测试绑定手机验证码错误"""
        # 模拟验证码验证失败
        mock_sms_service.verify_code.return_value = False

        result = auth_service.bind_phone(1, "13800138000", "wrong_code")

        assert result is None
        mock_user_repo.bind_phone.assert_not_called()

    def test_bind_phone_already_bound(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock
    ) -> None:
        """测试手机号已被绑定"""
        # 模拟验证码验证成功，但手机号已被其他用户绑定
        mock_sms_service.verify_code.return_value = True
        mock_user_repo.exists_by_phone.return_value = True

        result = auth_service.bind_phone(1, "13800138000", "123456")

        assert result is None
        mock_user_repo.bind_phone.assert_not_called()

    def test_unbind_phone_success(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试解绑手机成功"""
        # 模拟验证码验证成功，用户存在
        mock_sms_service.verify_code.return_value = True

        # 设置用户的手机号
        mock_user.phone = "13800138000"

        # 创建一个更新后的用户（phone 为 None）
        updated_user = MagicMock()
        updated_user.id = 1
        updated_user.username = "testuser"
        updated_user.phone = None
        updated_user.role = "user"
        updated_user.status = "active"
        updated_user.created_at = datetime.now()
        updated_user.updated_at = datetime.now()
        updated_user.last_login_at = None

        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.update.return_value = updated_user

        result = auth_service.unbind_phone(1, "123456")

        assert result is not None
        assert isinstance(result, UserResponse)
        assert result.phone is None

        # 验证更新手机号为 None
        mock_user_repo.update.assert_called_once_with(1, phone=None)

    def test_unbind_phone_invalid_code(
        self, auth_service: AuthService, mock_sms_service: MagicMock, mock_user_repo: MagicMock
    ) -> None:
        """测试解绑手机验证码错误"""
        # 模拟验证码验证失败
        mock_sms_service.verify_code.return_value = False

        result = auth_service.unbind_phone(1, "wrong_code")

        assert result is None
        mock_user_repo.update.assert_not_called()

    # ===== 辅助方法测试 =====

    def test_get_user_by_id_success(
        self, auth_service: AuthService, mock_user_repo: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试根据 ID 获取用户成功"""
        mock_user_repo.get_by_id.return_value = mock_user

        result = auth_service.get_user_by_id(1)

        assert result is not None
        assert isinstance(result, UserResponse)
        assert result.id == 1
        mock_user_repo.get_by_id.assert_called_once_with(1)

    def test_get_user_by_id_not_found(self, auth_service: AuthService, mock_user_repo: MagicMock) -> None:
        """测试根据 ID 获取用户不存在"""
        mock_user_repo.get_by_id.return_value = None

        result = auth_service.get_user_by_id(999)

        assert result is None
        mock_user_repo.get_by_id.assert_called_once_with(999)

    def test_validate_token_success(self, auth_service: AuthService, mock_jwt_handler: MagicMock) -> None:
        """测试验证 Token 成功"""
        # 模拟 Token 验证成功
        mock_payload = MagicMock()
        mock_payload.user_id = 1
        mock_payload.username = "testuser"
        mock_payload.role = "user"
        mock_jwt_handler.verify_token.return_value = mock_payload

        result = auth_service.validate_token("test_token")

        assert result is not None
        assert result["user_id"] == 1
        assert result["username"] == "testuser"
        assert result["role"] == "user"
        mock_jwt_handler.verify_token.assert_called_once_with("test_token")

    def test_validate_token_invalid(self, auth_service: AuthService, mock_jwt_handler: MagicMock) -> None:
        """测试验证 Token 无效"""
        # 模拟 Token 验证失败
        from jose import JWTError
        mock_jwt_handler.verify_token.side_effect = JWTError("Invalid token")

        result = auth_service.validate_token("invalid_token")

        assert result is None
        mock_jwt_handler.verify_token.assert_called_once_with("invalid_token")
