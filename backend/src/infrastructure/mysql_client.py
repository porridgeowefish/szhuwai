"""
MySQL 数据库客户端
==================

提供 MySQL 数据库连接池管理和会话控制。
"""

from contextlib import contextmanager
from typing import Generator

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.api.config import APIConfig


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类

    所有数据库模型都应继承此类。
    """
    pass


class MySQLClient:
    """MySQL 数据库客户端

    提供数据库连接池管理和会话上下文管理。

    Attributes:
        _config: API 配置实例
        _engine: SQLAlchemy 引擎
        _session_factory: 会话工厂

    Example:
        >>> client = MySQLClient(config)
        >>> with client.get_session() as session:
        ...     # 执行数据库操作
        ...     pass
    """

    def __init__(self, config: APIConfig) -> None:
        """初始化数据库连接

        Args:
            config: API 配置实例，包含 MySQL 连接参数
        """
        self._config = config

        # 构建数据库连接 URL
        database_url = (
            f"mysql+pymysql://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}"
            f"@{config.MYSQL_HOST}:{config.MYSQL_PORT}/{config.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

        # 创建引擎（带连接池）
        self._engine = create_engine(
            database_url,
            pool_size=config.MYSQL_POOL_SIZE,
            pool_pre_ping=True,  # 连接前检查可用性
            pool_recycle=3600,   # 连接回收时间（秒）
            echo=False,          # 不打印 SQL
        )

        # 创建会话工厂
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )

        logger.info(
            f"MySQL 客户端初始化完成: {config.MYSQL_HOST}:{config.MYSQL_PORT}"
            f"/{config.MYSQL_DATABASE}"
        )

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（上下文管理器）

        自动处理会话的提交和回滚。

        Yields:
            Session: SQLAlchemy 会话对象

        Example:
            >>> with client.get_session() as session:
            ...     session.execute(text("SELECT 1"))
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("数据库会话异常，已回滚")
            raise
        finally:
            session.close()

    def check_connection(self) -> bool:
        """检查数据库连接是否正常

        Returns:
            bool: 连接正常返回 True，否则返回 False
        """
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.debug("数据库连接检查成功")
            return True
        except SQLAlchemyError as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False

    def close(self) -> None:
        """关闭所有连接

        释放连接池中的所有连接。
        """
        self._engine.dispose()
        logger.info("数据库连接池已关闭")

    def create_tables(self) -> None:
        """创建所有表

        基于 Base 元数据创建所有定义的表。
        注意：生产环境建议使用迁移工具（如 Alembic）。
        """
        Base.metadata.create_all(self._engine)
        logger.info("数据库表创建完成")


# 全局实例
mysql_client: MySQLClient | None = None


def get_mysql_client() -> MySQLClient:
    """获取全局 MySQL 客户端实例

    Returns:
        MySQLClient: MySQL 客户端实例

    Raises:
        RuntimeError: 如果客户端未初始化

    Example:
        >>> client = get_mysql_client()
        >>> with client.get_session() as session:
        ...     pass
    """
    if mysql_client is None:
        raise RuntimeError("MySQL 客户端未初始化，请先调用 init_mysql_client()")
    return mysql_client


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（FastAPI 依赖注入）

    为 FastAPI 路由提供数据库会话的生成器函数。

    Yields:
        Session: SQLAlchemy 会话对象

    Example:
        >>> @app.get("/users")
        ... def get_users(db: Session = Depends(get_db)):
        ...     users = db.query(User).all()
        ...     return users
    """
    client = get_mysql_client()
    with client.get_session() as session:
        yield session


def init_mysql_client(config: APIConfig) -> MySQLClient:
    """初始化全局 MySQL 客户端

    Args:
        config: API 配置实例

    Returns:
        MySQLClient: 初始化后的 MySQL 客户端实例

    Example:
        >>> config = APIConfig.from_env()
        >>> client = init_mysql_client(config)
    """
    global mysql_client
    mysql_client = MySQLClient(config)
    return mysql_client
