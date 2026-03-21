"""
用户数据仓库
============

提供用户数据的 CRUD 操作。
"""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.user import UserCreate


class UserRepository:
    """用户数据仓库

    提供用户数据的创建、查询、更新和删除操作。

    Args:
        session: SQLAlchemy 数据库会话
    """

    def __init__(self, session: Session) -> None:
        """初始化仓库

        Args:
            session: 数据库会话
        """
        self.session = session

    def create(self, user_data: UserCreate, password_hash: str | None = None) -> User:
        """创建用户

        Args:
            user_data: 用户创建数据
            password_hash: 密码哈希（可选）

        Returns:
            创建的用户对象

        Raises:
            sqlalchemy.exc.IntegrityError: 用户名或手机号已存在
        """
        user = User(
            username=user_data.username,
            phone=user_data.phone,
            password_hash=password_hash,
            role=user_data.role,
            status=user_data.status,
        )
        self.session.add(user)
        self.session.flush()
        logger.info(f"创建用户成功: {user.id}")
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户

        Args:
            user_id: 用户 ID

        Returns:
            用户对象，不存在则返回 None
        """
        return (
            self.session.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )

    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            用户对象，不存在则返回 None
        """
        return (
            self.session.query(User)
            .filter(User.username == username, User.deleted_at.is_(None))
            .first()
        )

    def get_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户

        Args:
            phone: 手机号

        Returns:
            用户对象，不存在则返回 None
        """
        return (
            self.session.query(User)
            .filter(User.phone == phone, User.deleted_at.is_(None))
            .first()
        )

    def update(self, user_id: int, **kwargs: object) -> Optional[User]:
        """更新用户

        Args:
            user_id: 用户 ID
            **kwargs: 要更新的字段

        Returns:
            更新后的用户对象，用户不存在则返回 None
        """
        user = self.get_by_id(user_id)
        if user is None:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        self.session.flush()
        logger.info(f"更新用户: {user_id}, 字段: {list(kwargs.keys())}")
        return user

    def update_password(self, user_id: int, password_hash: str) -> bool:
        """更新密码

        Args:
            user_id: 用户 ID
            password_hash: 新的密码哈希

        Returns:
            更新成功返回 True，用户不存在返回 False
        """
        user = self.get_by_id(user_id)
        if user is None:
            return False

        user.password_hash = password_hash
        self.session.flush()
        logger.info(f"更新密码: {user_id}")
        return True

    def update_last_login(self, user_id: int) -> bool:
        """更新最后登录时间

        Args:
            user_id: 用户 ID

        Returns:
            更新成功返回 True，用户不存在返回 False
        """
        user = self.get_by_id(user_id)
        if user is None:
            return False

        user.last_login_at = datetime.now()
        self.session.flush()
        return True

    def bind_phone(self, user_id: int, phone: str) -> bool:
        """绑定手机号

        Args:
            user_id: 用户 ID
            phone: 手机号

        Returns:
            绑定成功返回 True，用户不存在返回 False

        Raises:
            sqlalchemy.exc.IntegrityError: 手机号已被其他用户绑定
        """
        user = self.get_by_id(user_id)
        if user is None:
            return False

        user.phone = phone
        self.session.flush()
        logger.info(f"绑定手机号: {user_id} -> {phone}")
        return True

    def update_status(self, user_id: int, status: str) -> bool:
        """更新状态

        Args:
            user_id: 用户 ID
            status: 新状态

        Returns:
            更新成功返回 True，用户不存在返回 False
        """
        user = self.get_by_id(user_id)
        if user is None:
            return False

        user.status = status
        self.session.flush()
        logger.info(f"更新用户状态: {user_id} -> {status}")
        return True

    def soft_delete(self, user_id: int) -> bool:
        """软删除用户

        Args:
            user_id: 用户 ID

        Returns:
            删除成功返回 True，用户不存在返回 False
        """
        user = self.get_by_id(user_id)
        if user is None:
            return False

        user.deleted_at = datetime.now()
        self.session.flush()
        logger.info(f"软删除用户: {user_id}")
        return True

    def list_users(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[User], int]:
        """获取用户列表（分页）

        Args:
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            (用户列表, 总数)
        """
        query = self.session.query(User).filter(User.deleted_at.is_(None))

        total = query.count()
        users = (
            query.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()
        )

        return users, total

    def exists_by_username(self, username: str) -> bool:
        """检查用户名是否存在

        Args:
            username: 用户名

        Returns:
            存在返回 True，否则返回 False
        """
        return (
            self.session.query(User)
            .filter(User.username == username, User.deleted_at.is_(None))
            .first()
            is not None
        )

    def exists_by_phone(self, phone: str) -> bool:
        """检查手机号是否存在

        Args:
            phone: 手机号

        Returns:
            存在返回 True，否则返回 False
        """
        return (
            self.session.query(User)
            .filter(User.phone == phone, User.deleted_at.is_(None))
            .first()
            is not None
        )
