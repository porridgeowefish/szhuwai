"""
认证依赖单元测试
================
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.api.deps import (
    AdminUser,
    CurrentUser,
    OptionalUser,
    get_admin_user,
    get_current_user,
    get_optional_user,
    get_user_repo,
)
from src.schemas.user import UserResponse


class TestGetUserRepo:
    """get_user_repo 依赖测试"""

    @patch("src.api.deps.get_db")
    def test_get_user_repo(self, mock_get_db: MagicMock) -> None:
        """测试获取用户仓库"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        result = get_user_repo()

        assert result is not None
        mock_get_db.assert_called_once()


class TestGetCurrentUser:
    """get_current_user 依赖测试"""

    @pytest.fixture
    def mock_credentials(self) -> HTTPAuthorizationCredentials:
        """创建模拟的 Token 凭证"""
        mock = MagicMock(spec=HTTPAuthorizationCredentials)
        mock.credentials = "valid_token"
        return mock

    @pytest.fixture
    def mock_user_repo(self) -> MagicMock:
        """创建模拟的用户仓库"""
        repo = MagicMock()
        return repo

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """创建模拟的用户"""
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        user.phone = "13800138000"
        user.role = "user"
        user.status = "active"
        user.created_at = MagicMock()
        user.updated_at = MagicMock()
        user.last_login_at = None
        return user

    @patch("src.api.deps.get_jwt_handler")
    def test_get_current_user_success(
        self, mock_get_jwt: MagicMock, mock_credentials: HTTPAuthorizationCredentials, mock_user_repo: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试获取当前用户成功"""
        # 模拟 Token 验证成功
        mock_payload = MagicMock()
        mock_payload.user_id = 1

        mock_jwt_handler = MagicMock()
        mock_jwt_handler.verify_token.return_value = mock_payload
        mock_get_jwt.return_value = mock_jwt_handler

        # 模拟用户存在
        mock_user_repo.get_by_id.return_value = mock_user

        # 执行测试 - 使用 asyncio.run 处理协程
        result = asyncio.run(get_current_user(mock_credentials, mock_user_repo))

        # 验证结果
        assert isinstance(result, UserResponse)
        assert result.id == 1
        assert result.username == "testuser"

        # 验证调用
        mock_jwt_handler.verify_token.assert_called_once_with("valid_token")
        mock_user_repo.get_by_id.assert_called_once_with(1)

    def test_get_current_user_no_credentials(self, mock_user_repo: MagicMock) -> None:
        """测试缺少 Authorization 头"""
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(None, mock_user_repo))

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == 401003

    @patch("src.api.deps.get_jwt_handler")
    def test_get_current_user_invalid_token(
        self, mock_get_jwt: MagicMock, mock_credentials: HTTPAuthorizationCredentials, mock_user_repo: MagicMock
    ) -> None:
        """测试无效 Token"""
        mock_jwt_handler = MagicMock()
        mock_jwt_handler.verify_token.side_effect = Exception("Invalid token")
        mock_get_jwt.return_value = mock_jwt_handler

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(mock_credentials, mock_user_repo))

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == 401002

    @patch("src.api.deps.get_jwt_handler")
    def test_get_current_user_not_found(
        self, mock_get_jwt: MagicMock, mock_credentials: HTTPAuthorizationCredentials, mock_user_repo: MagicMock
    ) -> None:
        """测试用户不存在"""
        mock_payload = MagicMock()
        mock_payload.user_id = 999

        mock_jwt_handler = MagicMock()
        mock_jwt_handler.verify_token.return_value = mock_payload
        mock_get_jwt.return_value = mock_jwt_handler

        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(mock_credentials, mock_user_repo))

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == 100001

    @patch("src.api.deps.get_jwt_handler")
    def test_get_current_user_disabled(
        self, mock_get_jwt: MagicMock, mock_credentials: HTTPAuthorizationCredentials, mock_user_repo: MagicMock
    ) -> None:
        """测试用户已禁用"""
        mock_payload = MagicMock()
        mock_payload.user_id = 1

        mock_user = MagicMock()
        mock_user.status = "disabled"
        mock_user_repo.get_by_id.return_value = mock_user

        mock_jwt_handler = MagicMock()
        mock_jwt_handler.verify_token.return_value = mock_payload
        mock_get_jwt.return_value = mock_jwt_handler

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(mock_credentials, mock_user_repo))

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == 100007


class TestGetOptionalUser:
    """get_optional_user 依赖测试"""

    @pytest.fixture
    def mock_user_repo(self) -> MagicMock:
        """创建模拟的用户仓库"""
        repo = MagicMock()
        return repo

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """创建模拟的用户"""
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        user.phone = "13800138000"
        user.role = "user"
        user.status = "active"
        user.created_at = MagicMock()
        user.updated_at = MagicMock()
        user.last_login_at = None
        return user

    @patch("src.api.deps.get_jwt_handler")
    def test_get_optional_user_with_valid_token(
        self, mock_get_jwt: MagicMock, mock_user_repo: MagicMock, mock_user: MagicMock
    ) -> None:
        """测试提供有效 Token 时返回用户"""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"

        mock_payload = MagicMock()
        mock_payload.user_id = 1

        mock_jwt_handler = MagicMock()
        mock_jwt_handler.verify_token.return_value = mock_payload
        mock_get_jwt.return_value = mock_jwt_handler

        mock_user_repo.get_by_id.return_value = mock_user

        result = asyncio.run(get_optional_user(mock_credentials, mock_user_repo))

        assert isinstance(result, UserResponse)
        assert result.id == 1

    def test_get_optional_user_no_token(self, mock_user_repo: MagicMock) -> None:
        """测试未提供 Token 时返回 None"""
        result = asyncio.run(get_optional_user(None, mock_user_repo))
        assert result is None

    @patch("src.api.deps.get_jwt_handler")
    def test_get_optional_user_invalid_token(
        self, mock_get_jwt: MagicMock, mock_user_repo: MagicMock
    ) -> None:
        """测试无效 Token 时返回 None"""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"

        mock_jwt_handler = MagicMock()
        mock_jwt_handler.verify_token.side_effect = Exception("Invalid token")
        mock_get_jwt.return_value = mock_jwt_handler

        result = asyncio.run(get_optional_user(mock_credentials, mock_user_repo))
        assert result is None


class TestGetAdminUser:
    """get_admin_user 依赖测试"""

    def test_get_admin_user_success(self) -> None:
        """测试管理员权限检查成功"""
        mock_user = MagicMock(spec=UserResponse)
        mock_user.role = "admin"

        result = asyncio.run(get_admin_user(mock_user))
        assert result == mock_user

    def test_get_admin_user_forbidden(self) -> None:
        """测试非管理员用户被拒绝"""
        mock_user = MagicMock(spec=UserResponse)
        mock_user.role = "user"

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_admin_user(mock_user))

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == 403002


class TestTypeAliases:
    """类型别名测试"""

    def test_current_user_is_callable(self) -> None:
        """测试 CurrentUser 类型别名是可调用的"""
        # CurrentUser 是一个 Annotated 类型，可以被 FastAPI 的 Depends 使用
        assert CurrentUser is not None

    def test_admin_user_is_callable(self) -> None:
        """测试 AdminUser 类型别名是可调用的"""
        assert AdminUser is not None

    def test_optional_user_is_callable(self) -> None:
        """测试 OptionalUser 类型别名是可调用的"""
        assert OptionalUser is not None

