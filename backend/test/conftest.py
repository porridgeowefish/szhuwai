"""
Pytest Configuration and Fixtures
==================================

This module provides pytest configuration and shared fixtures for all tests.
"""

from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

# Add project root to path
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 全局测试数据库引擎和会话工厂
_test_engine = None
_test_session_factory = None

# 全局测试报告存储（用于模拟 MongoDB）
_test_reports: dict[str, dict] = {}  # report_id -> report_data
_test_report_counter = 0  # 用于生成唯一的 report_id


def create_test_engine_and_session():
    """创建测试数据库引擎和会话工厂"""
    global _test_engine, _test_session_factory

    from src.infrastructure.mysql_client import Base
    from sqlalchemy.pool import StaticPool

    # 创建测试数据库引擎（使用 StaticPool 维持单一连接）
    _test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # 创建所有表
    Base.metadata.create_all(_test_engine)

    # 验证表已创建
    inspector = inspect(_test_engine)
    print(f"[conftest] 测试数据库表创建成功: {inspector.get_table_names()}")

    # 创建会话工厂
    _test_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

    return _test_engine, _test_session_factory


def _get_test_db():
    """获取测试数据库会话（用于替代 get_db）"""
    if _test_session_factory is None:
        create_test_engine_and_session()

    session = _test_session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# 在导入任何模块之前设置 mock
import src.infrastructure.mysql_client as mysql_module  # noqa: E402
_original_get_db = mysql_module.get_db
mysql_module.get_db = _get_test_db

# 也替换 auth 模块中的 get_db
try:
    import src.api.routes.auth as auth_module
    auth_module.get_db = _get_test_db
except ImportError:
    pass  # 模块可能还未导入


# ============ 数据库 Fixtures ============

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """每个测试会话开始时设置测试数据库"""
    print("[conftest] setup_test_database called")
    create_test_engine_and_session()
    yield
    # 清理
    global _test_engine, _test_session_factory
    if _test_engine:
        _test_engine.dispose()
        _test_engine = None
        _test_session_factory = None
    print("[conftest] setup_test_database cleanup done")


@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """每个测试后清理数据库"""
    global _test_reports, _test_report_counter
    yield
    # 清理所有表数据
    if _test_session_factory:
        session = _test_session_factory()
        try:
            from src.infrastructure.mysql_client import Base
            # 删除所有数据（保持表结构）
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        finally:
            session.close()
    # 清理测试报告
    _test_reports.clear()
    _test_report_counter = 0


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """创建测试数据库会话（用于需要直接访问数据库的测试）"""
    print("[conftest] db_session called")
    session = _test_session_factory()
    yield session
    session.close()
    print("[conftest] db_session closed")


# ============ FastAPI 测试客户端 Fixtures ============

@pytest.fixture
def client(mocker) -> TestClient:
    """创建 FastAPI 测试客户端"""
    from main import app
    from src.infrastructure.aliyun_sms_client import SmsSendResult

    # 全局验证码存储
    global _test_sms_codes_by_key, _test_sms_codes_latest, _test_reports, _test_report_counter, _template_to_scene
    _test_sms_codes_by_key.clear()
    _test_sms_codes_latest.clear()
    _template_to_scene.clear()
    _test_reports.clear()
    _test_report_counter = 0

    # Mock 全局 MySQL 客户端
    mock_mysql_client = mocker.MagicMock()
    mocker.patch("src.infrastructure.mysql_client.mysql_client", mock_mysql_client)
    mocker.patch("src.infrastructure.mysql_client.get_mysql_client", return_value=mock_mysql_client)

    # Mock JWT 客户端 - 使用真实的 JWT handler 来支持多用户
    from src.infrastructure.jwt_handler import JWTHandler
    from src.api.config import APIConfig

    jwt_config = APIConfig(
        JWT_SECRET_KEY="test_secret_key_for_testing_only",
        JWT_ALGORITHM="HS256",
        JWT_EXPIRE_SECONDS=3600
    )
    real_jwt_handler = JWTHandler(jwt_config)

    mock_jwt_handler = mocker.MagicMock()
    # 使用真实的 create_token 和 verify_token
    mock_jwt_handler.create_token = real_jwt_handler.create_token
    mock_jwt_handler.verify_token = real_jwt_handler.verify_token
    mocker.patch("src.infrastructure.jwt_handler.jwt_handler", mock_jwt_handler)
    mocker.patch("src.infrastructure.jwt_handler.get_jwt_handler", return_value=mock_jwt_handler)

    # Mock 短信客户端 - 记录发送的验证码
    def mock_send_verification_code(phone: str, code: str, template_id: str):
        """Mock 发送验证码，记录验证码到全局字典"""
        # 存储 (phone, template_id) -> code
        _test_sms_codes_by_key[(phone, template_id)] = code
        # 也存储 phone -> code 以便向后兼容
        _test_sms_codes_latest[phone] = code
        return SmsSendResult(success=True, biz_id="test_biz_id")

    def mock_get_template_id(scene: str) -> str:
        """Mock 获取模板 ID"""
        from src.api.config import APIConfig
        config = APIConfig()
        template_map = {
            "register": config.SMS_TEMPLATE_REGISTER,
            "login": config.SMS_TEMPLATE_LOGIN,
            "bind": config.SMS_TEMPLATE_BIND,
            "unbind": config.SMS_TEMPLATE_UNBIND,
            "reset_password": config.SMS_TEMPLATE_RESET_PASSWORD,
        }
        template_id = template_map.get(scene, "")
        # 存储双向映射
        _template_to_scene[template_id] = scene
        _template_to_scene[scene] = template_id  # scene -> template_id 映射
        return template_id

    mock_sms_client = mocker.MagicMock()
    mock_sms_client.send_verification_code = mock_send_verification_code
    mock_sms_client.get_template_id = mock_get_template_id
    mocker.patch("src.infrastructure.aliyun_sms_client.aliyun_sms_client", mock_sms_client)
    mocker.patch("src.infrastructure.aliyun_sms_client.get_aliyun_sms_client", return_value=mock_sms_client)

    # Mock MongoDB 客户端 - 配置报告存储
    mock_mongo_client = mocker.MagicMock()
    mock_db = mocker.MagicMock()
    mock_collection = mocker.MagicMock()

    # 模拟 insert_one
    def mock_insert_one(data):
        from bson import ObjectId
        from datetime import datetime, timezone
        global _test_report_counter
        _test_report_counter += 1
        # 生成有效的 ObjectId
        report_id = str(ObjectId())
        # 处理 ReportCreate 对象，转换为文档格式
        now = datetime.now(tz=timezone.utc)
        if hasattr(data, 'user_id'):  # ReportCreate 对象
            doc = {
                "_id": report_id,
                "user_id": data.user_id,
                "plan_name": data.plan_name,
                "trip_date": data.trip_date,
                "overall_rating": data.overall_rating,
                "content": data.content,
                "created_at": now,
                "deleted_at": None,
            }
        else:  # 直接的文档格式
            doc = {**data, "_id": report_id, "created_at": now, "deleted_at": None}
        _test_reports[report_id] = doc
        return MagicMock(inserted_id=report_id)

    mock_collection.insert_one = mock_insert_one

    # 模拟 count_documents
    def mock_count_documents(query):
        # 简单实现：返回所有报告数量（忽略查询条件）
        return len(_test_reports)

    mock_collection.count_documents = mock_count_documents

    # 模拟 find() 返回游标
    def mock_find(query=None):
        # 返回匹配的报告列表（过滤已删除的报告）
        reports = []
        for report in _test_reports.values():
            # 跳过已删除的报告
            if report.get("deleted_at") is not None:
                continue
            # 简单实现：忽略其他查询条件（实际应该检查 user_id 等）
            reports.append(report)

        # 创建模拟游标
        mock_cursor = MagicMock()

        def mock_skip(n):
            mock_cursor._skip = n
            return mock_cursor

        def mock_limit(n):
            mock_cursor._limit = n
            return mock_cursor

        def mock_sort(key, direction=None):
            mock_cursor._sort = key
            mock_cursor._direction = direction
            return mock_cursor

        def mock_iter():
            # 应用 skip、limit、sort
            result = reports.copy()
            if hasattr(mock_cursor, '_skip'):
                result = result[mock_cursor._skip:]
            if hasattr(mock_cursor, '_limit'):
                result = result[:mock_cursor._limit]
            return iter(result)

        mock_cursor.skip = mock_skip
        mock_cursor.limit = mock_limit
        mock_cursor.sort = mock_sort
        mock_cursor.__iter__ = lambda self: iter(mock_iter())

        return mock_cursor

    mock_collection.find = mock_find

    # 模拟 find_one
    def mock_find_one(query):
        # 处理查询条件
        if not query:
            return next(iter(_test_reports.values()), None)

        # 通过 report_id 查找
        if "_id" in query:
            report_id = str(query["_id"])
            report = _test_reports.get(report_id)

            # 检查报告是否存在且未删除
            if report and report.get("deleted_at") is not None:
                return None

            # 检查其他查询条件（如 user_id, deleted_at）
            if report:
                # 检查 user_id 条件
                if "user_id" in query and report.get("user_id") != query["user_id"]:
                    return None
                # 检查 deleted_at 条件
                if "deleted_at" in query:
                    if query["deleted_at"] is None and report.get("deleted_at") is not None:
                        return None
                    if query["deleted_at"] is not None and report.get("deleted_at") != query["deleted_at"]:
                        return None

            return report

        # 返回第一个匹配的报告（简化处理）
        for report in _test_reports.values():
            if report.get("deleted_at") is None:
                return report
        return None

    mock_collection.find_one = mock_find_one

    # 模拟 update_one
    def mock_update_one(query, update):
        # 简单实现：标记报告为已删除
        if "_id" in query:
            report_id = str(query["_id"])
            if report_id in _test_reports:
                _test_reports[report_id]["deleted_at"] = datetime.now(tz=timezone.utc).isoformat()
                return MagicMock(matched_count=1, modified_count=1)
        return MagicMock(matched_count=0, modified_count=0)

    mock_collection.update_one = mock_update_one

    # 配置 db 和 collection
    # 使用 __class__.__getitem__ 来避免 lambda 参数问题
    class MockDb:
        def __getitem__(self, name):
            return mock_collection

    mock_db = MockDb()
    mock_mongo_client.db = mock_db

    mocker.patch("src.infrastructure.mongo_client.mongo_client", mock_mongo_client)
    mocker.patch("src.infrastructure.mongo_client.get_mongo_client", return_value=mock_mongo_client)

    # Mock 主应用初始化函数
    mocker.patch("main.init_mysql_client")
    mocker.patch("main.init_jwt_handler")
    mocker.patch("main.init_aliyun_sms_client")
    mocker.patch("main.init_mongo_client")

    with TestClient(app) as test_client:
        yield test_client


# ============ Mock Fixtures ============

# 全局验证码存储（用于测试）
# _test_sms_codes_by_key: 按 (phone, template_id) 存储验证码
# _test_sms_codes_latest: 按 phone 存储最新的验证码（用于向后兼容）
_test_sms_codes_by_key: dict[tuple[str, str], str] = {}
_test_sms_codes_latest: dict[str, str] = {}
# 模板 ID 到场景的映射
_template_to_scene: dict[str, str] = {}


@pytest.fixture
def mock_sms():
    """Mock 短信发送辅助对象

    提供 get_sent_code 方法获取实际发送的验证码。
    验证码由 client fixture 中的 mock 自动记录。
    """
    class MockSmsHelper:
        def get_sent_code(self, phone: str, scene: str = None) -> str:
            """获取发送给指定手机号的验证码

            Args:
                phone: 手机号
                scene: 场景（可选，如果不提供则返回该手机号最新的验证码）

            Returns:
                验证码
            """
            if scene:
                # 优先使用已存储的 scene -> template_id 映射
                template_id = _template_to_scene.get(scene, "")
                if not template_id:
                    # 如果映射不存在，从配置获取
                    from src.api.config import APIConfig
                    config = APIConfig()
                    template_map = {
                        "register": config.SMS_TEMPLATE_REGISTER,
                        "login": config.SMS_TEMPLATE_LOGIN,
                        "bind": config.SMS_TEMPLATE_BIND,
                        "unbind": config.SMS_TEMPLATE_UNBIND,
                        "reset_password": config.SMS_TEMPLATE_RESET_PASSWORD,
                    }
                    template_id = template_map.get(scene, "")
                return _test_sms_codes_by_key.get((phone, template_id), "123456")
            # 如果没有指定场景，返回该手机号最新的验证码
            return _test_sms_codes_latest.get(phone, "123456")

        def get_all_codes(self) -> dict[tuple[str, str], str]:
            """获取所有验证码"""
            return dict(_test_sms_codes_by_key)

    return MockSmsHelper()


@pytest.fixture
def mock_jwt(mocker):
    """Mock JWT 处理器

    使用固定的密钥和较短的过期时间，方便测试。
    """
    mock_handler = mocker.MagicMock()
    mock_handler.generate_token.return_value = "test_jwt_token_12345"
    mock_handler.verify_token.return_value = MagicMock(
        user_id=1,
        username="testuser",
        role="user",
        exp=int((datetime.now(tz=timezone.utc) + timedelta(hours=1)).timestamp())
    )
    return mock_handler


# ============ 测试数据 Fixtures ============

@pytest.fixture
def test_user_data() -> dict:
    """测试用户数据"""
    return {
        "username": "testuser001",
        "password": "Test@123456"
    }


@pytest.fixture
def test_phone() -> str:
    """测试手机号"""
    return "13800138000"


@pytest.fixture
def test_sms_code() -> str:
    """测试验证码（与 Mock 短信服务返回的验证码一致）"""
    return "123456"


@pytest.fixture
def create_test_user(db_session: Session):
    """工厂函数：创建测试用户

    Returns:
        Callable: 创建用户的函数
    """
    def _create_user(
        username: str = "testuser",
        password: str = "password123",
        phone: str | None = None,
        role: str = "user",
        status: str = "active"
    ):
        """创建用户

        Args:
            username: 用户名
            password: 密码（明文，会自动加密）
            phone: 手机号（可选）
            role: 角色
            status: 状态

        Returns:
            User: 创建的用户对象
        """
        from src.infrastructure.password_hasher import PasswordHasher
        from src.models.user import User

        hasher = PasswordHasher()
        password_hash = hasher.hash_password(password)

        user = User(
            username=username,
            phone=phone,
            password_hash=password_hash,
            role=role,
            status=status,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc)
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    return _create_user


@pytest.fixture
def auth_headers(client: TestClient, test_user_data: dict) -> dict:
    """认证请求头

    自动注册并登录用户，返回包含 Token 的请求头。
    """
    # 注册
    client.post("/api/v1/auth/register", json=test_user_data)

    # 登录
    response = client.post("/api/v1/auth/login", json=test_user_data)
    data = response.json()

    token = data["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client: TestClient, create_test_user) -> dict:
    """管理员认证请求头"""
    # 创建管理员用户
    _ = create_test_user(
        username="admin",
        password="admin123",
        role="admin",
        status="active"
    )

    # 登录
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    data = response.json()

    token = data["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


# ============ 原有 Fixtures ============

@pytest.fixture(scope="session")
def project_path():
    """Return the project root directory path."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_path):
    """Return the test data directory path."""
    data_path = project_path / "test_data"
    data_path.mkdir(exist_ok=True)
    return data_path


@pytest.fixture
def sample_point():
    """Return a sample Point3D object for testing."""
    from src.schemas.base import Point3D
    return Point3D(lat=39.9042, lon=116.4074, elevation=50)


@pytest.fixture
def sample_track_data(sample_point):
    """Return sample track analysis data."""
    from src.schemas.track import TrackAnalysisResult
    from src.schemas.base import Point3D
    return TrackAnalysisResult(
        total_distance_km=10.5,
        total_ascent_m=250,
        total_descent_m=50,
        max_elevation_m=350,
        min_elevation_m=100,
        avg_elevation_m=200,
        start_point=sample_point,
        end_point=Point3D(lat=39.91, lon=116.41, elevation=300),
        max_elev_point=Point3D(lat=39.905, lon=116.405, elevation=350),
        min_elev_point=sample_point,
        difficulty_score=65,
        difficulty_level="困难",
        estimated_duration_hours=3.5,
        safety_risk="中等风险",
        track_points_count=1000
    )


@pytest.fixture
def sample_weather_data():
    """Return sample weather data."""
    from src.schemas.weather import WeatherDaily
    return WeatherDaily(
        fxDate="2024-03-15",
        tempMax=25.5,
        tempMin=15.2,
        textDay="晴",
        textNight="晴",
        windScaleDay="3",
        windScaleNight="2",
        humidity=65,
        precipitation=0,
        pop=10,
        uvIndex=6,
        visibility=20
    )


@pytest.fixture
def mock_api_response():
    """Return a mock API response for testing."""
    return {
        "code": "200",
        "status": "1",
        "updateTime": "2024-03-10 12:00:00"
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests that require API keys"
    )
    config.addinivalue_line(
        "markers", "auth: marks authentication tests"
    )
