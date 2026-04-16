"""Redis 客户端配置和初始化"""

import redis
from typing import Optional
from loguru import logger

# 全局 Redis 客户端实例
_redis_client: Optional[redis.Redis] = None


class InMemoryRedis:
    """Redis 不可用时的内存降级实现"""

    def __init__(self):
        self._store: dict = {}

    def set(self, key: str, value: str, ex: int = None) -> bool:
        self._store[key] = value
        return True

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def delete(self, key: str) -> int:
        existed = key in self._store
        self._store.pop(key, None)
        return 1 if existed else 0

    def exists(self, key: str) -> bool:
        return key in self._store

    def ping(self) -> bool:
        return True


def init_redis_client(config) -> object:
    """初始化 Redis 客户端，不可用时降级到内存实现"""
    global _redis_client

    try:
        _redis_client = redis.Redis(
            host=getattr(config, "REDIS_HOST", "localhost"),
            port=getattr(config, "REDIS_PORT", 6379),
            db=getattr(config, "REDIS_DB", 0),
            password=getattr(config, "REDIS_PASSWORD", None),
            decode_responses=True,
        )
        # 测试连接
        _redis_client.ping()
        logger.info("Redis 客户端初始化成功")
    except Exception as e:
        logger.warning(f"Redis 客户端初始化失败，降级到内存模式: {e}")
        _redis_client = InMemoryRedis()

    return _redis_client


def get_redis() -> object:
    """获取 Redis 客户端实例（保证非 None）"""
    if _redis_client is None:
        logger.warning("Redis 未初始化，创建内存降级实例")
        return InMemoryRedis()
    return _redis_client
