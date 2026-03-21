"""
MongoDB 数据库客户端
====================

提供 MongoDB 数据库连接管理和集合访问。
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError
from typing import Any

from loguru import logger

from src.api.config import APIConfig


class MongoClientWrapper:
    """MongoDB 数据库客户端包装器

    提供 MongoDB 连接管理和集合访问功能。

    Attributes:
        _config: API 配置实例
        _client: PyMongo 客户端实例

    Example:
        >>> client = MongoClientWrapper(config)
        >>> collection = client.get_collection("reports")
        >>> for doc in collection.find():
        ...     print(doc)
        >>> client.close()
    """

    _client: MongoClient

    def __init__(self, config: APIConfig) -> None:
        """初始化 MongoDB 连接

        Args:
            config: API 配置实例，包含 MongoDB 连接参数

        支持无认证连接（开发环境）和认证连接（生产环境）。
        """
        self._config = config

        # 构建连接 URI
        if config.MONGO_USER and config.MONGO_PASSWORD:
            # 带认证的连接
            uri = (
                f"mongodb://{config.MONGO_USER}:{config.MONGO_PASSWORD}"
                f"@{config.MONGO_HOST}:{config.MONGO_PORT}"
            )
        else:
            # 无认证连接（开发环境）
            uri = f"mongodb://{config.MONGO_HOST}:{config.MONGO_PORT}"

        # 创建客户端
        self._client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,  # 5秒超时
            connectTimeoutMS=5000,
        )

        logger.info(
            f"MongoDB 客户端初始化完成: {config.MONGO_HOST}:{config.MONGO_PORT}"
            f"/{config.MONGO_DATABASE}"
        )

    @property
    def db(self) -> Database[Any]:
        """获取数据库实例

        Returns:
            Database: MongoDB 数据库对象
        """
        return self._client[self._config.MONGO_DATABASE]

    def get_collection(self, name: str) -> Any:
        """获取集合

        Args:
            name: 集合名称

        Returns:
            Collection: MongoDB 集合对象
        """
        return self.db[name]

    def check_connection(self) -> bool:
        """检查数据库连接是否正常

        Returns:
            bool: 连接正常返回 True，否则返回 False
        """
        try:
            # 执行简单命令测试连接
            self._client.admin.command("ping")
            logger.debug("MongoDB 连接检查成功")
            return True
        except (ConnectionFailure, PyMongoError) as e:
            logger.error(f"MongoDB 连接检查失败: {e}")
            return False

    def close(self) -> None:
        """关闭连接

        释放 MongoDB 客户端连接。
        """
        self._client.close()
        logger.info("MongoDB 连接已关闭")


# 全局实例
mongo_client: MongoClientWrapper | None = None


def get_mongo_client() -> MongoClientWrapper:
    """获取全局 MongoDB 客户端实例

    Returns:
        MongoClientWrapper: MongoDB 客户端实例

    Raises:
        RuntimeError: 如果客户端未初始化

    Example:
        >>> client = get_mongo_client()
        >>> collection = client.get_collection("reports")
    """
    if mongo_client is None:
        raise RuntimeError("MongoDB 客户端未初始化，请先调用 init_mongo_client()")
    return mongo_client


def init_mongo_client(config: APIConfig) -> MongoClientWrapper:
    """初始化全局 MongoDB 客户端

    Args:
        config: API 配置实例

    Returns:
        MongoClientWrapper: 初始化后的 MongoDB 客户端实例

    Example:
        >>> config = APIConfig.from_env()
        >>> client = init_mongo_client(config)
    """
    global mongo_client
    mongo_client = MongoClientWrapper(config)
    return mongo_client
