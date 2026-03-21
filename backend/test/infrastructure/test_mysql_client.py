"""
MySQL 客户端测试
================

测试 MySQL 数据库连接和会话管理功能。
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from src.api.config import APIConfig
from src.infrastructure.mysql_client import (
    MySQLClient,
    Base,
    get_mysql_client,
    init_mysql_client,
)


class TestMySQLClient:
    """MySQL 客户端测试"""

    @pytest.fixture
    def mock_config(self) -> APIConfig:
        """创建模拟配置"""
        return APIConfig(
            MYSQL_HOST="localhost",
            MYSQL_PORT=3306,
            MYSQL_USER="test_user",
            MYSQL_PASSWORD="test_password",
            MYSQL_DATABASE="test_db",
            MYSQL_POOL_SIZE=5,
        )

    @pytest.fixture
    def mock_engine(self) -> MagicMock:
        """创建模拟引擎"""
        engine = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock()
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        return engine

    def test_init_with_config(self, mock_config: APIConfig, mock_engine: MagicMock) -> None:
        """测试使用配置初始化"""
        with patch(
            "src.infrastructure.mysql_client.create_engine", return_value=mock_engine
        ):
            client = MySQLClient(mock_config)

            assert client._config == mock_config
            assert client._engine is not None

    def test_init_creates_engine_with_correct_url(
        self, mock_config: APIConfig
    ) -> None:
        """测试初始化时创建正确的数据库连接 URL"""
        with patch(
            "src.infrastructure.mysql_client.create_engine"
        ) as mock_create_engine:
            mock_create_engine.return_value = MagicMock()

            MySQLClient(mock_config)

            # 验证 create_engine 被调用，并检查 URL 格式
            call_args = mock_create_engine.call_args
            assert call_args is not None
            url = call_args[0][0]
            assert "mysql+pymysql://" in url
            assert "test_user" in url
            assert "test_password" in url
            assert "localhost" in url
            assert "3306" in url
            assert "test_db" in url

    def test_check_connection_success(
        self, mock_config: APIConfig, mock_engine: MagicMock
    ) -> None:
        """测试连接检查成功"""
        with patch(
            "src.infrastructure.mysql_client.create_engine", return_value=mock_engine
        ):
            client = MySQLClient(mock_config)
            result = client.check_connection()

            assert result is True
            mock_engine.connect.assert_called_once()

    def test_check_connection_failure(
        self, mock_config: APIConfig, mock_engine: MagicMock
    ) -> None:
        """测试连接检查失败"""
        mock_engine.connect.side_effect = SQLAlchemyError("Connection failed")

        with patch(
            "src.infrastructure.mysql_client.create_engine", return_value=mock_engine
        ):
            client = MySQLClient(mock_config)
            result = client.check_connection()

            assert result is False

    def test_get_session_context_manager(
        self, mock_config: APIConfig, mock_engine: MagicMock
    ) -> None:
        """测试会话上下文管理器"""
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        with patch(
            "src.infrastructure.mysql_client.create_engine", return_value=mock_engine
        ):
            with patch(
                "src.infrastructure.mysql_client.sessionmaker"
            ) as mock_sessionmaker:
                mock_sessionmaker.return_value.return_value = mock_session

                client = MySQLClient(mock_config)

                with client.get_session() as session:
                    assert session is not None

    def test_get_session_rollback_on_exception(
        self, mock_config: APIConfig, mock_engine: MagicMock
    ) -> None:
        """测试会话在异常时回滚"""
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        with patch(
            "src.infrastructure.mysql_client.create_engine", return_value=mock_engine
        ):
            with patch(
                "src.infrastructure.mysql_client.sessionmaker"
            ) as mock_sessionmaker:
                mock_sessionmaker.return_value.return_value = mock_session

                client = MySQLClient(mock_config)

                with pytest.raises(ValueError):
                    with client.get_session():
                        raise ValueError("Test error")

                mock_session.rollback.assert_called_once()

    def test_close_connections(
        self, mock_config: APIConfig, mock_engine: MagicMock
    ) -> None:
        """测试关闭连接"""
        with patch(
            "src.infrastructure.mysql_client.create_engine", return_value=mock_engine
        ):
            client = MySQLClient(mock_config)
            client.close()

            mock_engine.dispose.assert_called_once()

    def test_pool_size_configuration(
        self, mock_config: APIConfig, mock_engine: MagicMock
    ) -> None:
        """测试连接池大小配置"""
        with patch(
            "src.infrastructure.mysql_client.create_engine"
        ) as mock_create_engine:
            mock_create_engine.return_value = mock_engine

            MySQLClient(mock_config)

            # 验证连接池参数
            call_kwargs = mock_create_engine.call_args[1]
            assert call_kwargs.get("pool_size") == 5
            assert call_kwargs.get("pool_pre_ping") is True


class TestMySQLClientGlobal:
    """全局 MySQL 客户端实例测试"""

    def teardown_method(self) -> None:
        """每个测试后重置全局实例"""
        import src.infrastructure.mysql_client as module

        module.mysql_client = None

    def test_init_mysql_client(self) -> None:
        """测试初始化全局客户端"""
        config = APIConfig(
            MYSQL_HOST="localhost",
            MYSQL_PORT=3306,
            MYSQL_USER="root",
            MYSQL_PASSWORD="password",
            MYSQL_DATABASE="test_db",
        )

        with patch("src.infrastructure.mysql_client.create_engine"):
            client = init_mysql_client(config)

            assert client is not None
            assert isinstance(client, MySQLClient)

    def test_get_mysql_client_after_init(self) -> None:
        """测试初始化后获取全局客户端"""
        config = APIConfig(
            MYSQL_HOST="localhost",
            MYSQL_PORT=3306,
            MYSQL_USER="root",
            MYSQL_PASSWORD="password",
            MYSQL_DATABASE="test_db",
        )

        with patch("src.infrastructure.mysql_client.create_engine"):
            init_mysql_client(config)
            client = get_mysql_client()

            assert client is not None

    def test_get_mysql_client_without_init_raises_error(self) -> None:
        """测试未初始化时获取客户端抛出异常"""
        import src.infrastructure.mysql_client as module

        module.mysql_client = None

        with pytest.raises(RuntimeError, match="MySQL 客户端未初始化"):
            get_mysql_client()


class TestBase:
    """SQLAlchemy 基类测试"""

    def test_base_is_declarative_base(self) -> None:
        """测试 Base 是声明式基类"""
        from sqlalchemy.orm import DeclarativeBase

        assert issubclass(Base, DeclarativeBase)

    def test_base_has_metadata(self) -> None:
        """测试 Base 有 metadata 属性"""
        assert hasattr(Base, "metadata")
