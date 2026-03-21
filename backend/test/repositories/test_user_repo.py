"""
用户仓库测试
============
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.infrastructure.mysql_client import Base
from src.models.user import User
from src.repositories.user_repo import UserRepository
from src.schemas.user import UserCreate


@pytest.fixture
def in_memory_engine():
    """内存数据库引擎"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(in_memory_engine) -> Session:
    """测试数据库会话"""
    SessionLocal = sessionmaker(bind=in_memory_engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def user_repo(db_session: Session) -> UserRepository:
    """用户仓库实例"""
    return UserRepository(db_session)


class TestUserRepositoryCreate:
    """创建用户测试"""

    def test_create_user_with_username(self, user_repo: UserRepository) -> None:
        """测试用户名注册"""
        user_data = UserCreate(username="testuser", password="password123")
        password_hash = "$2b$12$abcdef1234567890abcdef1234567890abcdef1234567890abcd"

        user = user_repo.create(user_data, password_hash)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.password_hash == password_hash
        assert user.role == "user"
        assert user.status == "active"
        assert user.created_at is not None

    def test_create_user_with_phone(self, user_repo: UserRepository) -> None:
        """测试手机号注册"""
        user_data = UserCreate(phone="13800138000", password="password123")
        password_hash = "$2b$12$abcdef1234567890abcdef1234567890abcdef1234567890abcd"

        user = user_repo.create(user_data, password_hash)

        assert user.id is not None
        assert user.phone == "13800138000"
        assert user.password_hash == password_hash

    def test_create_user_with_custom_role(self, user_repo: UserRepository) -> None:
        """测试自定义角色"""
        user_data = UserCreate(username="admin", password="password123", role="admin")
        password_hash = "$2b$12$abcdef1234567890abcdef1234567890abcdef1234567890abcd"

        user = user_repo.create(user_data, password_hash)

        assert user.role == "admin"


class TestUserRepositoryQuery:
    """查询用户测试"""

    def test_get_by_id(self, user_repo: UserRepository) -> None:
        """测试根据 ID 获取"""
        user_data = UserCreate(username="testuser", password="password123")
        created = user_repo.create(user_data, "$2b$12$hash")

        user = user_repo.get_by_id(created.id)

        assert user is not None
        assert user.id == created.id
        assert user.username == "testuser"

    def test_get_by_id_not_found(self, user_repo: UserRepository) -> None:
        """测试根据 ID 获取不存在的用户"""
        user = user_repo.get_by_id(99999)
        assert user is None

    def test_get_by_username(self, user_repo: UserRepository) -> None:
        """测试根据用户名获取"""
        user_data = UserCreate(username="testuser", password="password123")
        user_repo.create(user_data, "$2b$12$hash")

        user = user_repo.get_by_username("testuser")

        assert user is not None
        assert user.username == "testuser"

    def test_get_by_username_not_found(self, user_repo: UserRepository) -> None:
        """测试根据用户名获取不存在的用户"""
        user = user_repo.get_by_username("nonexistent")
        assert user is None

    def test_get_by_phone(self, user_repo: UserRepository) -> None:
        """测试根据手机号获取"""
        user_data = UserCreate(phone="13800138000", password="password123")
        user_repo.create(user_data, "$2b$12$hash")

        user = user_repo.get_by_phone("13800138000")

        assert user is not None
        assert user.phone == "13800138000"

    def test_get_by_phone_not_found(self, user_repo: UserRepository) -> None:
        """测试根据手机号获取不存在的用户"""
        user = user_repo.get_by_phone("19999999999")
        assert user is None


class TestUserRepositoryUpdate:
    """更新用户测试"""

    def test_update_password(self, user_repo: UserRepository) -> None:
        """测试更新密码"""
        user_data = UserCreate(username="testuser", password="password123")
        user = user_repo.create(user_data, "$2b$12$oldhash")
        new_hash = "$2b$12$newhash12345678901234567890123456789012345678901234567"

        success = user_repo.update_password(user.id, new_hash)
        updated = user_repo.get_by_id(user.id)

        assert success is True
        assert updated.password_hash == new_hash

    def test_update_last_login(self, user_repo: UserRepository) -> None:
        """测试更新最后登录时间"""
        user_data = UserCreate(username="testuser", password="password123")
        user = user_repo.create(user_data, "$2b$12$hash")

        success = user_repo.update_last_login(user.id)
        updated = user_repo.get_by_id(user.id)

        assert success is True
        assert updated.last_login_at is not None
        assert isinstance(updated.last_login_at, datetime)

    def test_bind_phone(self, user_repo: UserRepository) -> None:
        """测试绑定手机号"""
        user_data = UserCreate(username="testuser", password="password123")
        user = user_repo.create(user_data, "$2b$12$hash")

        success = user_repo.bind_phone(user.id, "13900139000")
        updated = user_repo.get_by_id(user.id)

        assert success is True
        assert updated.phone == "13900139000"

    def test_update_status(self, user_repo: UserRepository) -> None:
        """测试更新状态"""
        user_data = UserCreate(username="testuser", password="password123")
        user = user_repo.create(user_data, "$2b$12$hash")

        success = user_repo.update_status(user.id, "inactive")
        updated = user_repo.get_by_id(user.id)

        assert success is True
        assert updated.status == "inactive"

    def test_update_multiple_fields(self, user_repo: UserRepository) -> None:
        """测试更新多个字段"""
        user_data = UserCreate(username="testuser", password="password123")
        user = user_repo.create(user_data, "$2b$12$hash")

        updated = user_repo.update(user.id, role="admin", status="active")

        assert updated is not None
        assert updated.role == "admin"
        assert updated.status == "active"

    def test_update_nonexistent_user(self, user_repo: UserRepository) -> None:
        """测试更新不存在的用户"""
        result = user_repo.update(99999, role="admin")
        assert result is None


class TestUserRepositoryDelete:
    """删除用户测试"""

    def test_soft_delete(self, user_repo: UserRepository) -> None:
        """测试软删除用户"""
        user_data = UserCreate(username="testuser", password="password123")
        user = user_repo.create(user_data, "$2b$12$hash")

        success = user_repo.soft_delete(user.id)

        # 软删除后，get_by_id 应该返回 None
        not_found = user_repo.get_by_id(user.id)
        assert success is True
        assert not_found is None

        # 直接查询数据库验证 deleted_at 已设置
        deleted_user = user_repo.session.query(User).filter(User.id == user.id).first()
        assert deleted_user is not None
        assert deleted_user.deleted_at is not None

    def test_soft_delete_nonexistent_user(self, user_repo: UserRepository) -> None:
        """测试软删除不存在的用户"""
        success = user_repo.soft_delete(99999)
        assert success is False


class TestUserRepositoryList:
    """列表查询测试"""

    def test_list_users_pagination(self, user_repo: UserRepository) -> None:
        """测试分页查询"""
        # 创建 25 个用户
        for i in range(25):
            user_data = UserCreate(username=f"user{i}", password="password123")
            user_repo.create(user_data, "$2b$12$hash")

        users, total = user_repo.list_users(page=1, page_size=10)

        assert total == 25
        assert len(users) == 10
        assert users[0].username == "user0"

    def test_list_users_second_page(self, user_repo: UserRepository) -> None:
        """测试第二页"""
        for i in range(25):
            user_data = UserCreate(username=f"user{i}", password="password123")
            user_repo.create(user_data, "$2b$12$hash")

        users, total = user_repo.list_users(page=2, page_size=10)

        assert total == 25
        assert len(users) == 10
        assert users[0].username == "user10"

    def test_list_users_empty(self, user_repo: UserRepository) -> None:
        """测试空列表"""
        users, total = user_repo.list_users()

        assert total == 0
        assert len(users) == 0


class TestUserRepositoryExists:
    """存在性检查测试"""

    def test_exists_by_username(self, user_repo: UserRepository) -> None:
        """测试检查用户名存在"""
        user_data = UserCreate(username="testuser", password="password123")
        user_repo.create(user_data, "$2b$12$hash")

        assert user_repo.exists_by_username("testuser") is True
        assert user_repo.exists_by_username("nonexistent") is False

    def test_exists_by_phone(self, user_repo: UserRepository) -> None:
        """测试检查手机号存在"""
        user_data = UserCreate(phone="13800138000", password="password123")
        user_repo.create(user_data, "$2b$12$hash")

        assert user_repo.exists_by_phone("13800138000") is True
        assert user_repo.exists_by_phone("19999999999") is False


class TestUserRepositoryConstraints:
    """约束测试"""

    def test_duplicate_username_raises_error(self, user_repo: UserRepository) -> None:
        """测试重复用户名应该抛出异常"""
        user_data = UserCreate(username="testuser", password="password123")
        user_repo.create(user_data, "$2b$12$hash")

        # 尝试创建相同用户名
        duplicate_data = UserCreate(username="testuser", password="password456")
        with pytest.raises(Exception):  # IntegrityError
            user_repo.create(duplicate_data, "$2b$12$hash2")

    def test_duplicate_phone_raises_error(self, user_repo: UserRepository) -> None:
        """测试重复手机号应该抛出异常"""
        user_data = UserCreate(phone="13800138000", password="password123")
        user_repo.create(user_data, "$2b$12$hash")

        # 尝试创建相同手机号
        duplicate_data = UserCreate(phone="13800138000", password="password456")
        with pytest.raises(Exception):  # IntegrityError
            user_repo.create(duplicate_data, "$2b$12$hash2")
