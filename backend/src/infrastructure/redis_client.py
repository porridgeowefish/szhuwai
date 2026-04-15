"""Redis 客户端配置和初始化"""

import redis
from typing import Optional
from loguru import logger

# 全局 Redis 客户端实例
_redis_client: Optional[redis.Redis] = None


def init_redis_client(config) -> redis.Redis:
    """初始化 Redis 客户端"""
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
        logger.warning(f"Redis 客户端初始化失败: {e}")
        _redis_client = None

    return _redis_client


def get_redis() -> Optional[redis.Redis]:
    """获取 Redis 客户端实例"""
    return _redis_client
