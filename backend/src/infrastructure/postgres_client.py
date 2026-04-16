"""PostgreSQL + PostGIS 客户端"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from loguru import logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.api.config import APIConfig


class PostgresBase(DeclarativeBase):
    """PostgreSQL ORM 基类"""
    pass


class PostgresClient:
    """PostgreSQL 客户端（异步）"""

    def __init__(self, config: "APIConfig") -> None:
        url = (
            f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}"
            f"@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DATABASE}"
        )
        self.engine = create_async_engine(url, pool_size=5, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_tables(self) -> None:
        """创建所有表（包括 PostGIS 扩展）"""
        async with self.engine.begin() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS postgis")
            )
            await conn.run_sync(PostgresBase.metadata.create_all)
        logger.info("PostgreSQL tables created")


# 全局实例
_postgres_client: PostgresClient | None = None


def init_postgres_client(config: "APIConfig") -> PostgresClient:
    global _postgres_client
    _postgres_client = PostgresClient(config)
    return _postgres_client


def get_postgres_client() -> PostgresClient:
    if _postgres_client is None:
        raise ValueError("PostgreSQL 客户端未初始化")
    return _postgres_client
