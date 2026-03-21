"""
短信验证码仓库测试
==================
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.infrastructure.mysql_client import Base
from src.models.sms_code import SmsCode
from src.models.sms_send_log import SmsSendLog
from src.repositories.sms_code_repo import SmsCodeRepository
from src.repositories.sms_log_repo import SmsLogRepository


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
def sms_code_repo(db_session: Session) -> SmsCodeRepository:
    """验证码仓库实例"""
    return SmsCodeRepository(db_session)


@pytest.fixture
def sms_log_repo(db_session: Session) -> SmsLogRepository:
    """发送日志仓库实例"""
    return SmsLogRepository(db_session)


class TestSmsCodeRepositoryCreate:
    """创建验证码测试"""

    def test_create_code(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试创建验证码"""
        code = sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="register",
            expire_seconds=300
        )

        assert code.id is not None
        assert code.phone == "13800138000"
        assert code.code == "123456"
        assert code.scene == "register"
        assert code.used == 0
        assert code.expire_at is not None
        assert code.created_at is not None

    def test_create_code_with_custom_expire(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试创建自定义过期时间的验证码"""
        code = sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="login",
            expire_seconds=600
        )

        now = datetime.now()
        expire_diff = (code.expire_at - now).total_seconds()

        # 允许 5 秒误差
        assert 595 <= expire_diff <= 605


class TestSmsCodeRepositoryQuery:
    """查询验证码测试"""

    def test_get_valid_code(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试获取有效验证码"""
        sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="register",
            expire_seconds=300
        )

        code = sms_code_repo.get_valid_code("13800138000", "register")

        assert code is not None
        assert code.phone == "13800138000"
        assert code.code == "123456"
        assert code.used == 0

    def test_get_valid_code_expired(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试获取过期验证码返回 None"""
        # 创建一个已过期的验证码
        code = sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="register",
            expire_seconds=300
        )
        # 手动设置为过期
        code.expire_at = datetime.now() - timedelta(seconds=10)
        sms_code_repo.session.flush()

        result = sms_code_repo.get_valid_code("13800138000", "register")

        assert result is None

    def test_get_valid_code_used(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试获取已使用验证码返回 None"""
        code = sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="register",
            expire_seconds=300
        )
        code.used = 1
        sms_code_repo.session.flush()

        result = sms_code_repo.get_valid_code("13800138000", "register")

        assert result is None

    def test_get_valid_code_not_found(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试获取不存在的验证码"""
        result = sms_code_repo.get_valid_code("19999999999", "register")

        assert result is None

    def test_get_valid_code_wrong_scene(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试获取错误场景的验证码"""
        sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="register",
            expire_seconds=300
        )

        result = sms_code_repo.get_valid_code("13800138000", "login")

        assert result is None


class TestSmsCodeRepositoryMarkUsed:
    """标记已使用测试"""

    def test_mark_used(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试标记已使用"""
        code = sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="register",
            expire_seconds=300
        )

        success = sms_code_repo.mark_used(code.id)

        assert success is True
        # 刷新查询验证
        sms_code_repo.session.refresh(code)
        assert code.used == 1

    def test_mark_used_nonexistent(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试标记不存在的验证码"""
        success = sms_code_repo.mark_used(99999)

        assert success is False


class TestSmsCodeRepositoryVerify:
    """验证验证码测试"""

    def test_verify_code_success(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试验证成功"""
        sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="register",
            expire_seconds=300
        )

        success = sms_code_repo.verify_code("13800138000", "123456", "register")

        assert success is True

    def test_verify_code_wrong(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试验证失败（错误验证码）"""
        sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="register",
            expire_seconds=300
        )

        success = sms_code_repo.verify_code("13800138000", "999999", "register")

        assert success is False

    def test_verify_code_expired(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试验证失败（已过期）"""
        code = sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="register",
            expire_seconds=300
        )
        code.expire_at = datetime.now() - timedelta(seconds=10)
        sms_code_repo.session.flush()

        success = sms_code_repo.verify_code("13800138000", "123456", "register")

        assert success is False

    def test_verify_code_not_found(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试验证不存在的验证码"""
        success = sms_code_repo.verify_code("19999999999", "123456", "register")

        assert success is False

    def test_verify_code_marks_used(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试验证后标记为已使用"""
        sms_code_repo.create(
            phone="13800138000",
            code="123456",
            scene="register",
            expire_seconds=300
        )

        sms_code_repo.verify_code("13800138000", "123456", "register")

        # 再次验证应该失败
        success = sms_code_repo.verify_code("13800138000", "123456", "register")
        assert success is False


class TestSmsCodeRepositoryDeleteExpired:
    """清理过期验证码测试"""

    def test_delete_expired(self, sms_code_repo: SmsCodeRepository) -> None:
        """测试清理过期验证码"""
        # 创建三个验证码：一个有效，两个过期
        valid_code = sms_code_repo.create(
            phone="13800138000",
            code="111111",
            scene="register",
            expire_seconds=300
        )

        expired1 = sms_code_repo.create(
            phone="13800138001",
            code="222222",
            scene="register",
            expire_seconds=300
        )
        expired1.expire_at = datetime.now() - timedelta(seconds=10)
        sms_code_repo.session.flush()

        expired2 = sms_code_repo.create(
            phone="13800138002",
            code="333333",
            scene="register",
            expire_seconds=300
        )
        expired2.expire_at = datetime.now() - timedelta(seconds=10)
        sms_code_repo.session.flush()

        deleted_count = sms_code_repo.delete_expired()

        assert deleted_count == 2

        # 验证有效验证码仍然存在
        assert sms_code_repo.get_valid_code("13800138000", "register") is not None


class TestSmsLogRepositoryCreate:
    """创建日志测试"""

    def test_create_log_success(self, sms_log_repo: SmsLogRepository) -> None:
        """测试创建成功日志"""
        sms_log_repo.create(
            phone="13800138000",
            scene="register",
            ip="127.0.0.1",
            success=True
        )

        # 验证日志已创建
        from src.models.sms_send_log import SmsSendLog
        log = sms_log_repo.session.query(SmsSendLog).first()

        assert log is not None
        assert log.phone == "13800138000"
        assert log.scene == "register"
        assert log.ip == "127.0.0.1"
        assert log.success == 1
        assert log.error_msg is None

    def test_create_log_failure(self, sms_log_repo: SmsLogRepository) -> None:
        """测试创建失败日志"""
        sms_log_repo.create(
            phone="13800138000",
            scene="register",
            ip="127.0.0.1",
            success=False,
            error_msg="服务超时"
        )

        from src.models.sms_send_log import SmsSendLog
        log = sms_log_repo.session.query(SmsSendLog).first()

        assert log is not None
        assert log.success == 0
        assert log.error_msg == "服务超时"


class TestSmsLogRepositoryCount:
    """统计发送次数测试"""

    def test_count_today_empty(self, sms_log_repo: SmsLogRepository) -> None:
        """测试今日无发送记录"""
        count = sms_log_repo.count_today_by_phone("13800138000")

        assert count == 0

    def test_count_today(self, sms_log_repo: SmsLogRepository) -> None:
        """测试统计今日发送次数"""
        sms_log_repo.create("13800138000", "register", "127.0.0.1", True)
        sms_log_repo.create("13800138000", "login", "127.0.0.1", True)
        sms_log_repo.create("13800138000", "register", "127.0.0.1", True)

        count = sms_log_repo.count_today_by_phone("13800138000")

        assert count == 3

    def test_count_today_different_phone(self, sms_log_repo: SmsLogRepository) -> None:
        """测试统计不同手机号"""
        sms_log_repo.create("13800138000", "register", "127.0.0.1", True)
        sms_log_repo.create("13900139000", "register", "127.0.0.1", True)

        count = sms_log_repo.count_today_by_phone("13800138000")

        assert count == 1


class TestSmsLogRepositoryLatestTime:
    """最近发送时间测试"""

    def test_get_latest_time_empty(self, sms_log_repo: SmsLogRepository) -> None:
        """测试无发送记录"""
        result = sms_log_repo.get_latest_by_phone("13800138000")

        assert result is None

    def test_get_latest_time(self, sms_log_repo: SmsLogRepository) -> None:
        """测试获取最近发送时间"""
        sms_log_repo.create("13800138000", "register", "127.0.0.1", True)

        latest_time = sms_log_repo.get_latest_by_phone("13800138000")

        assert latest_time is not None
        assert isinstance(latest_time, datetime)

    def test_get_latest_time_multiple(self, sms_log_repo: SmsLogRepository) -> None:
        """测试多次发送获取最新时间"""
        sms_log_repo.create("13800138000", "register", "127.0.0.1", True)
        sms_log_repo.create("13800138000", "login", "127.0.0.1", True)

        latest_time = sms_log_repo.get_latest_by_phone("13800138000")

        assert latest_time is not None
        # 验证是最新的时间
        from src.models.sms_send_log import SmsSendLog
        logs = sms_log_repo.session.query(SmsSendLog).filter(
            SmsSendLog.phone == "13800138000"
        ).order_by(SmsSendLog.created_at.desc()).all()
        assert latest_time == logs[0].created_at
