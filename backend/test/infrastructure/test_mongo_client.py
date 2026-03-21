"""
MongoDB 客户端测试
==================

测试 MongoDB 数据库连接和集合管理功能。
"""

import pytest
from unittest.mock import patch, MagicMock
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from src.api.config import APIConfig
from src.infrastructure.mongo_client import (
    MongoClientWrapper,
    get_mongo_client,
    init_mongo_client,
)


class TestMongoClientWrapper:
    """MongoDB 客户端测试"""

    @pytest.fixture
    def mock_config(self) -> APIConfig:
        """创建模拟配置"""
        return APIConfig(
            MONGO_HOST="localhost",
            MONGO_PORT=27017,
            MONGO_USER="",
            MONGO_PASSWORD="",
            MONGO_DATABASE="test_db",
        )

    @pytest.fixture
    def mock_config_with_auth(self) -> APIConfig:
        """创建带认证的模拟配置"""
        return APIConfig(
            MONGO_HOST="localhost",
            MONGO_PORT=27017,
            MONGO_USER="test_user",
            MONGO_PASSWORD="test_password",
            MONGO_DATABASE="test_db",
        )

    @pytest.fixture
    def mock_mongo_client(self) -> MagicMock:
        """创建模拟 MongoDB 客户端"""
        client = MagicMock()
        mock_db = MagicMock()
        client.__getitem__ = MagicMock(return_value=mock_db)
        client.close = MagicMock()
        return client

    def test_init_without_auth(
        self, mock_config: APIConfig, mock_mongo_client: MagicMock
    ) -> None:
        """测试无认证配置初始化"""
        with patch(
            "src.infrastructure.mongo_client.MongoClient",
            return_value=mock_mongo_client
        ):
            client = MongoClientWrapper(mock_config)

            assert client._config == mock_config
            assert client._client is not None

    def test_init_with_auth(
        self, mock_config_with_auth: APIConfig, mock_mongo_client: MagicMock
    ) -> None:
        """测试带认证配置初始化"""
        with patch(
            "src.infrastructure.mongo_client.MongoClient",
            return_value=mock_mongo_client
        ) as mock_client_class:
            client = MongoClientWrapper(mock_config_with_auth)

            # 验证 MongoClient 被正确调用
            call_args = mock_client_class.call_args
            assert call_args is not None
            # 检查 URI 格式包含认证信息
            uri = call_args[0][0]
            assert "mongodb://" in uri
            assert "test_user" in uri
            assert "test_password" in uri

    def test_init_creates_correct_uri_without_auth(
        self, mock_config: APIConfig
    ) -> None:
        """测试无认证时创建正确的连接 URI"""
        with patch("src.infrastructure.mongo_client.MongoClient") as mock_client_class:
            mock_client_class.return_value = MagicMock()

            MongoClientWrapper(mock_config)

            # 验证 MongoClient 被调用，并检查 URI 格式
            call_args = mock_client_class.call_args
            assert call_args is not None
            uri = call_args[0][0]
            assert "mongodb://localhost:27017" in uri

    def test_check_connection_success(
        self, mock_config: APIConfig, mock_mongo_client: MagicMock
    ) -> None:
        """测试连接检查成功"""
        with patch(
            "src.infrastructure.mongo_client.MongoClient",
            return_value=mock_mongo_client
        ):
            client = MongoClientWrapper(mock_config)
            result = client.check_connection()

            assert result is True

    def test_check_connection_failure_server_timeout(
        self, mock_config: APIConfig, mock_mongo_client: MagicMock
    ) -> None:
        """测试连接检查失败（服务器超时）"""
        mock_mongo_client.admin.command.side_effect = ServerSelectionTimeoutError(
            "Connection timeout"
        )

        with patch(
            "src.infrastructure.mongo_client.MongoClient",
            return_value=mock_mongo_client
        ):
            client = MongoClientWrapper(mock_config)
            result = client.check_connection()

            assert result is False

    def test_check_connection_failure_connection_error(
        self, mock_config: APIConfig, mock_mongo_client: MagicMock
    ) -> None:
        """测试连接检查失败（连接错误）"""
        mock_mongo_client.admin.command.side_effect = ConnectionFailure(
            "Connection failed"
        )

        with patch(
            "src.infrastructure.mongo_client.MongoClient",
            return_value=mock_mongo_client
        ):
            client = MongoClientWrapper(mock_config)
            result = client.check_connection()

            assert result is False

    def test_get_database_property(
        self, mock_config: APIConfig, mock_mongo_client: MagicMock
    ) -> None:
        """测试获取数据库实例"""
        mock_db = MagicMock()
        mock_mongo_client.__getitem__ = MagicMock(return_value=mock_db)

        with patch(
            "src.infrastructure.mongo_client.MongoClient",
            return_value=mock_mongo_client
        ):
            client = MongoClientWrapper(mock_config)
            db = client.db

            assert db is not None
            mock_mongo_client.__getitem__.assert_called_with("test_db")

    def test_get_collection(
        self, mock_config: APIConfig, mock_mongo_client: MagicMock
    ) -> None:
        """测试获取集合"""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_mongo_client.__getitem__ = MagicMock(return_value=mock_db)

        with patch(
            "src.infrastructure.mongo_client.MongoClient",
            return_value=mock_mongo_client
        ):
            client = MongoClientWrapper(mock_config)
            collection = client.get_collection("test_collection")

            assert collection is not None
            mock_db.__getitem__.assert_called_with("test_collection")

    def test_close_connection(
        self, mock_config: APIConfig, mock_mongo_client: MagicMock
    ) -> None:
        """测试关闭连接"""
        with patch(
            "src.infrastructure.mongo_client.MongoClient",
            return_value=mock_mongo_client
        ):
            client = MongoClientWrapper(mock_config)
            client.close()

            mock_mongo_client.close.assert_called_once()


class TestMongoClientGlobal:
    """全局 MongoDB 客户端实例测试"""

    def teardown_method(self) -> None:
        """每个测试后重置全局实例"""
        import src.infrastructure.mongo_client as module

        module.mongo_client = None

    def test_init_mongo_client(self) -> None:
        """测试初始化全局客户端"""
        config = APIConfig(
            MONGO_HOST="localhost",
            MONGO_PORT=27017,
            MONGO_DATABASE="test_db",
        )

        with patch("src.infrastructure.mongo_client.MongoClient"):
            client = init_mongo_client(config)

            assert client is not None
            assert isinstance(client, MongoClientWrapper)

    def test_get_mongo_client_after_init(self) -> None:
        """测试初始化后获取全局客户端"""
        config = APIConfig(
            MONGO_HOST="localhost",
            MONGO_PORT=27017,
            MONGO_DATABASE="test_db",
        )

        with patch("src.infrastructure.mongo_client.MongoClient"):
            init_mongo_client(config)
            client = get_mongo_client()

            assert client is not None

    def test_get_mongo_client_without_init_raises_error(self) -> None:
        """测试未初始化时获取客户端抛出异常"""
        import src.infrastructure.mongo_client as module

        module.mongo_client = None

        with pytest.raises(RuntimeError, match="MongoDB 客户端未初始化"):
            get_mongo_client()
