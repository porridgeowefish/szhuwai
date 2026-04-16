"""
Redis 客户端
============

提供 Redis 连接管理，支持内存降级用于开发测试。
"""

import time
from typing import TYPE_CHECKING, Optional

from loguru import logger

if TYPE_CHECKING:
    from src.api.config import APIConfig


class InMemoryBackend:
    """内存后端，Redis 不可用时的降级方案

    模拟 Redis 基本操作，数据不跨进程共享。
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float]] = {}  # key → (value, expire_at)
        self._counters: dict[str, int] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        expire_at = time.time() + ex if ex else float("inf")
        self._store[key] = (value, expire_at)

    def get(self, key: str) -> str | None:
        if key in self._store:
            value, expire_at = self._store[key]
            if time.time() < expire_at:
                return value
            del self._store[key]
        return None

    def delete(self, key: str) -> int:
        count = 1 if key in self._store else 0
        self._store.pop(key, None)
        self._counters.pop(key, None)
        return count

    def incr(self, key: str) -> int:
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]

    def expire(self, key: str, seconds: int) -> bool:
        return key in self._counters or key in self._store

    def ttl(self, key: str) -> int:
        if key in self._store:
            _, expire_at = self._store[key]
            remaining = int(expire_at - time.time())
            return max(remaining, -1)
        return -1

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def getdel(self, key: str) -> str | None:
        """获取并删除（模拟 GETDEL）"""
        value = self.get(key)
        if value is not None:
            self.delete(key)
        return value

    def ping(self) -> bool:
        return True


# 全局实例
_redis_client: "InMemoryBackend | object | None" = None


def init_redis_client(config: "APIConfig") -> InMemoryBackend | object:
    """初始化 Redis 客户端，不可用时降级到内存后端

    Args:
        config: API 配置对象

    Returns:
        Redis 客户端实例（或内存后端）
    """
    global _redis_client
    try:
        import redis

        _redis_client = redis.Redis(
            host=getattr(config, "REDIS_HOST", "localhost"),
            port=getattr(config, "REDIS_PORT", 6379),
            password=getattr(config, "REDIS_PASSWORD", None) or None,
            db=getattr(config, "REDIS_DB", 0),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        # 测试连接
        _redis_client.ping()
        logger.info("Redis 连接成功")
    except Exception as e:
        logger.warning(f"Redis 连接失败，使用内存后端: {e}")
        _redis_client = InMemoryBackend()
    return _redis_client


# 别名，兼容旧代码
init_redis = init_redis_client


def get_redis() -> InMemoryBackend | object:
    """获取 Redis 客户端实例（保证非 None）

    如果未初始化则自动创建内存降级实例。
    """
    global _redis_client
    if _redis_client is None:
        logger.warning("Redis 未初始化，创建内存降级实例")
        _redis_client = InMemoryBackend()
    return _redis_client
