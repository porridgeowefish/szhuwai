"""
Infrastructure 模块
==================

提供基础设施层服务，包括数据库连接、缓存等。
"""

from src.infrastructure.mysql_client import (
    MySQLClient,
    Base,
    get_mysql_client,
    init_mysql_client,
)
from src.infrastructure.mongo_client import (
    MongoClientWrapper,
    get_mongo_client,
    init_mongo_client,
)
from src.infrastructure.jwt_handler import (
    JWTHandler,
    TokenPayload,
    get_jwt_handler,
    init_jwt_handler,
)
from src.infrastructure.password_hasher import (
    PasswordHasher,
    get_password_hasher,
    password_hasher,
)

__all__ = [
    "MySQLClient",
    "Base",
    "get_mysql_client",
    "init_mysql_client",
    "MongoClientWrapper",
    "get_mongo_client",
    "init_mongo_client",
    "JWTHandler",
    "TokenPayload",
    "get_jwt_handler",
    "init_jwt_handler",
    "PasswordHasher",
    "get_password_hasher",
    "password_hasher",
]
