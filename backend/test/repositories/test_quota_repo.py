"""
额度仓库测试
============
"""

import pytest
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.infrastructure.mysql_client import Base
from src.models.user import User
from src.models.quota_usage import QuotaUsage
from src.repositories.quota_repo import QuotaRepository
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


@pytest.fixture
def quota_repo(db_session: Session) -> QuotaRepository:
    """额度仓库实例"""
    return QuotaRepository(db_session)


@pytest.fixture
def test_user(user_repo: UserRepository) -> User:
    """测试用户"""
    user_data = UserCreate(username="testuser", password="password123")
    return user_repo.create(user_data, "$2b$12$hash")


class TestQuotaRepositoryGetOrCreate:
    """获取或创建记录测试"""

    def test_get_or_create_new(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试创建新记录"""
        today = date.today()

        quota = quota_repo.get_or_create(test_user.id, today)

        assert quota.id is not None
        assert quota.user_id == test_user.id
        assert quota.usage_date == today
        assert quota.usage_count == 0

    def test_get_or_create_existing(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试获取已存在记录"""
        today = date.today()

        # 第一次创建
        quota1 = quota_repo.get_or_create(test_user.id, today)
        quota1.usage_count = 5

        # 第二次获取
        quota2 = quota_repo.get_or_create(test_user.id, today)

        # 应该返回同一个记录
        assert quota1.id == quota2.id
        assert quota2.usage_count == 5

    def test_get_or_create_default_date(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试默认使用当天日期"""
        quota = quota_repo.get_or_create(test_user.id)

        assert quota.usage_date == date.today()


class TestQuotaRepositoryGetUsage:
    """获取使用次数测试"""

    def test_get_usage_zero(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试获取初始使用次数为0"""
        quota_repo.get_or_create(test_user.id)

        usage = quota_repo.get_usage(test_user.id)

        assert usage == 0

    def test_get_usage_after_increment(
        self, quota_repo: QuotaRepository, test_user: User
    ) -> None:
        """测试增加后获取使用次数"""
        quota_repo.get_or_create(test_user.id)
        quota_repo.increment_usage(test_user.id)

        usage = quota_repo.get_usage(test_user.id)

        assert usage == 1


class TestQuotaRepositoryIncrementUsage:
    """增加使用次数测试"""

    def test_increment_usage_once(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试增加使用次数一次"""
        quota_repo.get_or_create(test_user.id)

        new_count = quota_repo.increment_usage(test_user.id)

        assert new_count == 1

    def test_increment_usage_multiple(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试增加使用次数多次"""
        quota_repo.get_or_create(test_user.id)

        count1 = quota_repo.increment_usage(test_user.id)
        count2 = quota_repo.increment_usage(test_user.id)
        count3 = quota_repo.increment_usage(test_user.id)

        assert count1 == 1
        assert count2 == 2
        assert count3 == 3

    def test_increment_usage_persists(
        self, quota_repo: QuotaRepository, test_user: User, db_session: Session
    ) -> None:
        """测试增加后持久化"""
        quota_repo.get_or_create(test_user.id)
        quota_repo.increment_usage(test_user.id)

        # 直接查询数据库验证
        usage = (
            db_session.query(QuotaUsage)
            .filter(
                QuotaUsage.user_id == test_user.id,
                QuotaUsage.usage_date == date.today(),
            )
            .first()
        )

        assert usage is not None
        assert usage.usage_count == 1


class TestQuotaRepositoryCheckQuota:
    """检查额度测试"""

    def test_check_quota_available(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试检查额度充足"""
        quota_repo.get_or_create(test_user.id)

        has_quota, remaining = quota_repo.check_quota(test_user.id, max_count=2)

        assert has_quota is True
        assert remaining == 2

    def test_check_quota_exhausted(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试检查额度耗尽"""
        quota_repo.get_or_create(test_user.id)
        # 用完额度
        quota_repo.increment_usage(test_user.id)
        quota_repo.increment_usage(test_user.id)

        has_quota, remaining = quota_repo.check_quota(test_user.id, max_count=2)

        assert has_quota is False
        assert remaining == 0

    def test_check_quota_partially_used(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试部分使用额度"""
        quota_repo.get_or_create(test_user.id)
        quota_repo.increment_usage(test_user.id)

        has_quota, remaining = quota_repo.check_quota(test_user.id, max_count=3)

        assert has_quota is True
        assert remaining == 2

    def test_check_quota_default_max(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试默认最大额度"""
        quota_repo.get_or_create(test_user.id)

        has_quota, remaining = quota_repo.check_quota(test_user.id)

        assert has_quota is True
        assert remaining == 2  # DEFAULT_DAILY_QUOTA


class TestQuotaRepositoryResetIfNewDay:
    """日期重置测试"""

    def test_reset_if_new_day_creates_new(
        self, quota_repo: QuotaRepository, test_user: User
    ) -> None:
        """测试新的一天创建新记录"""
        yesterday = date.today() - timedelta(days=1)
        yesterday_quota = quota_repo.get_or_create(test_user.id, yesterday)
        yesterday_quota.usage_count = 5

        # 检查今天是否创建新记录
        is_new = quota_repo.reset_if_new_day(test_user.id)

        assert is_new is True

        # 验证今天的记录独立
        today_usage = quota_repo.get_usage(test_user.id)
        assert today_usage == 0

    def test_reset_if_new_day_same_day(
        self, quota_repo: QuotaRepository, test_user: User
    ) -> None:
        """测试同一天不创建新记录"""
        quota_repo.get_or_create(test_user.id)

        is_new = quota_repo.reset_if_new_day(test_user.id)

        assert is_new is False


class TestQuotaRepositoryDateIsolation:
    """日期隔离测试"""

    def test_usage_by_date(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试按日期隔离使用记录"""
        yesterday = date.today() - timedelta(days=1)
        today = date.today()

        # 昨天使用 5 次
        quota_repo.get_or_create(test_user.id, yesterday)
        for _ in range(5):
            quota_repo.increment_usage(test_user.id, yesterday)

        # 今天使用 2 次
        quota_repo.get_or_create(test_user.id, today)
        for _ in range(2):
            quota_repo.increment_usage(test_user.id, today)

        # 验证各自独立
        yesterday_usage = quota_repo.get_usage(test_user.id, yesterday)
        today_usage = quota_repo.get_usage(test_user.id, today)

        assert yesterday_usage == 5
        assert today_usage == 2

    def test_check_quota_by_date(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试按日期检查额度"""
        yesterday = date.today() - timedelta(days=1)
        today = date.today()

        # 昨天用完额度
        quota_repo.get_or_create(test_user.id, yesterday)
        for _ in range(2):
            quota_repo.increment_usage(test_user.id, yesterday)

        # 今天应该有全新额度
        has_quota, remaining = quota_repo.check_quota(test_user.id, max_count=2)

        assert has_quota is True
        assert remaining == 2


class TestQuotaRepositoryUniqueConstraint:
    """唯一约束测试"""

    def test_unique_constraint(self, quota_repo: QuotaRepository, test_user: User) -> None:
        """测试用户+日期唯一约束"""
        today = date.today()

        quota_repo.get_or_create(test_user.id, today)
        quota_repo.increment_usage(test_user.id, today)

        # 再次获取同一天应该返回同一记录
        quota_repo.get_or_create(test_user.id, today)
        usage = quota_repo.get_usage(test_user.id, today)

        assert usage == 1  # 不是 2

    def test_different_users_same_date(
        self, quota_repo: QuotaRepository, user_repo: UserRepository
    ) -> None:
        """测试不同用户同一天独立记录"""
        user1 = user_repo.create(UserCreate(username="user1", password="pass123"), "$2b$12$hash")
        user2 = user_repo.create(UserCreate(username="user2", password="pass123"), "$2b$12$hash")
        today = date.today()

        quota_repo.get_or_create(user1.id, today)
        quota_repo.increment_usage(user1.id, today)

        quota_repo.get_or_create(user2.id, today)
        quota_repo.increment_usage(user2.id, today)

        # 两者应该独立
        usage1 = quota_repo.get_usage(user1.id, today)
        usage2 = quota_repo.get_usage(user2.id, today)

        assert usage1 == 1
        assert usage2 == 1
