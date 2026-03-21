# TASK-005 用户数据模型与仓库

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 1 天 |
| 前置任务 | TASK-001（MySQL 连接） |
| 后继任务 | TASK-009 |

## 任务目标

实现用户数据模型（SQLAlchemy ORM）和数据访问仓库（Repository），支持用户的 CRUD 操作。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/models/__init__.py` | 新建，导出数据模型 |
| `src/models/user.py` | 新建，用户 ORM 模型 |
| `src/repositories/__init__.py` | 新建，导出仓库 |
| `src/repositories/user_repo.py` | 新建，用户数据仓库 |
| `src/schemas/user.py` | 新建，用户 Pydantic 模型 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/infrastructure/mysql_client.py` | 由 TASK-001 负责 |
| `src/infrastructure/__init__.py` | 由 TASK-001 负责扩展 |
| 现有 `src/schemas/*.py` | 保持现有模型不变 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/models/__init__.py` | ORM 模型模块 |
| `src/models/user.py` | 用户 ORM 模型 |
| `src/repositories/__init__.py` | 仓库模块 |
| `src/repositories/user_repo.py` | 用户数据仓库 |
| `src/schemas/user.py` | 用户 Pydantic 模型 |
| `test/models/__init__.py` | 测试目录 |
| `test/repositories/__init__.py` | 测试目录 |
| `test/repositories/test_user_repo.py` | 单元测试 |

## 技术规格

### ORM 模型

```python
# src/models/user.py
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.mysql_client import Base


class User(Base):
    """用户表 ORM 模型"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

### Pydantic 模型

```python
# src/schemas/user.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UserBase(BaseModel):
    """用户基础模型"""
    username: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    role: str = Field(default="user", max_length=20)
    status: str = Field(default="active", max_length=20)


class UserCreate(UserBase):
    """用户创建模型"""
    password: Optional[str] = Field(None, min_length=6, max_length=32)


class UserResponse(UserBase):
    """用户响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    @property
    def phone_masked(self) -> str | None:
        """脱敏后的手机号"""
        if self.phone:
            return self.phone[:3] + "****" + self.phone[-4:]
        return None


class UserInDB(UserResponse):
    """数据库中的用户（含敏感信息）"""
    password_hash: Optional[str] = None
```

### Repository 接口

```python
# src/repositories/user_repo.py
from typing import Optional
from sqlalchemy.orm import Session
from src.models.user import User
from src.schemas.user import UserCreate


class UserRepository:
    """用户数据仓库"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, user_data: UserCreate, password_hash: str | None = None) -> User:
        """创建用户"""
        pass

    def get_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        pass

    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        pass

    def get_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        pass

    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """更新用户"""
        pass

    def update_password(self, user_id: int, password_hash: str) -> bool:
        """更新密码"""
        pass

    def update_last_login(self, user_id: int) -> bool:
        """更新最后登录时间"""
        pass

    def bind_phone(self, user_id: int, phone: str) -> bool:
        """绑定手机号"""
        pass

    def update_status(self, user_id: int, status: str) -> bool:
        """更新状态"""
        pass

    def soft_delete(self, user_id: int) -> bool:
        """软删除用户"""
        pass

    def list_users(self, page: int = 1, page_size: int = 20) -> tuple[list[User], int]:
        """获取用户列表（分页）"""
        pass

    def exists_by_username(self, username: str) -> bool:
        """检查用户名是否存在"""
        pass

    def exists_by_phone(self, phone: str) -> bool:
        """检查手机号是否存在"""
        pass
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| MySQLClient | TASK-001 | 待完成 |
| SQLAlchemy Base | TASK-001 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/repositories/test_user_repo.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """测试数据库会话"""
    # 使用内存数据库
    pass


class TestUserRepository:
    """用户仓库测试"""

    def test_create_user_with_username(self, db_session):
        """测试用户名注册"""
        pass

    def test_create_user_with_phone(self, db_session):
        """测试手机号注册"""
        pass

    def test_get_by_id(self, db_session):
        """测试根据 ID 获取"""
        pass

    def test_get_by_username(self, db_session):
        """测试根据用户名获取"""
        pass

    def test_get_by_phone(self, db_session):
        """测试根据手机号获取"""
        pass

    def test_update_password(self, db_session):
        """测试更新密码"""
        pass

    def test_bind_phone(self, db_session):
        """测试绑定手机"""
        pass

    def test_update_status(self, db_session):
        """测试更新状态"""
        pass

    def test_exists_by_username(self, db_session):
        """测试检查用户名存在"""
        pass

    def test_exists_by_phone(self, db_session):
        """测试检查手机号存在"""
        pass

    def test_list_users_pagination(self, db_session):
        """测试分页查询"""
        pass
```

**测试用例清单**：
- [ ] 用户名注册成功
- [ ] 手机号注册成功
- [ ] 根据各字段查询成功
- [ ] 更新密码成功
- [ ] 绑定手机成功
- [ ] 更新状态成功
- [ ] 软删除成功
- [ ] 分页查询正确
- [ ] 唯一性检查正确

### Step 2: 实现功能

1. 创建 `src/models/user.py` ORM 模型
2. 创建 `src/schemas/user.py` Pydantic 模型
3. 创建 `src/repositories/user_repo.py` 数据仓库
4. 更新各 `__init__.py` 导出

### Step 3: 验证通过

```bash
# 运行测试
pytest test/repositories/test_user_repo.py -v

# 代码检查
ruff check src/models/ src/repositories/ src/schemas/user.py
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）
- [ ] 无破坏性变更（现有测试仍通过）

## 参考资源

### 现有代码参考

| 文件 | 参考内容 |
|------|----------|
| `src/schemas/base.py` | Pydantic 模型风格 |
| `src/api/config.py` | Pydantic Field 用法 |

### 相关文档

- [ITERATION_AUTH_PLAN.md - 4.2.1 users 表](../ITERATION_AUTH_PLAN.md#421-users用户表)
- [SQLAlchemy 2.0 ORM](https://docs.sqlalchemy.org/en/20/orm/)

## 注意事项

1. **密码存储**: 只存储 password_hash，不存储明文密码
2. **软删除**: 使用 deleted_at 字段，不物理删除
3. **手机号脱敏**: 响应中返回脱敏后的手机号
4. **唯一性**: username 和 phone 都需要唯一性检查
