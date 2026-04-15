"""
Redis 客户端
============

提供 Redis 连接管理，支持 Mock 模式用于开发测试。
"""

from typing import TYPE_CHECKING

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
        import time

        expire_at = time.time() + ex if ex else float("inf")
        self._store[key] = (value, expire_at)

    def get(self, key: str) -> str | None:
        import time

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
        import time

        # 清理过期计数器
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]

    def expire(self, key: str, seconds: int) -> bool:
        # 内存后端简化：计数器不支持独立 TTL
        return key in self._counters or key in self._store

    def ttl(self, key: str) -> int:
        import time

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


# 全局实例
_redis_client: "InMemoryBackend | object | None" = None


def init_redis(config: "APIConfig") -> InMemoryBackend | object:
    """初始化 Redis 客户端

    Args:
        config: API 配置对象

    Returns:
        Redis 客户端实例（或内存后端）
    """
    global _redis_client
    try:
        import redis

        _redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            password=config.REDIS_PASSWORD or None,
            db=config.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        # 测试连接
        _redis_client.ping()
        logger.info(f"Redis 连接成功: {config.REDIS_HOST}:{config.REDIS_PORT}")
    except Exception as e:
        logger.warning(f"Redis 连接失败，使用内存后端: {e}")
        _redis_client = InMemoryBackend()
    return _redis_client


def get_redis() -> InMemoryBackend | object:
    """获取 Redis 客户端实例

    Returns:
        Redis 客户端实例

    Raises:
        ValueError: 当客户端未初始化时
    """
    if _redis_client is None:
        raise ValueError("Redis 客户端未初始化，请先调用 init_redis()")
    return _redis_client
