# TASK-001 MySQL 数据库连接

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 预估工时 | 0.5 天 |
| 前置任务 | 无 |
| 后继任务 | TASK-005, TASK-006 |

## 任务目标

实现 MySQL 数据库连接基础设施，提供统一的数据访问接口，支持连接池管理。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/infrastructure/__init__.py` | 新建，导出数据库客户端 |
| `src/infrastructure/mysql_client.py` | 新建，MySQL 连接管理 |
| `src/api/config.py` | 扩展，添加 MySQL 配置项 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `main.py` | 入口文件，其他任务负责集成 |
| `test/conftest.py` | 由 TASK-012 统一扩展 |
| 现有 `src/api/routes/*.py` | 保持现有 API 不变 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/infrastructure/__init__.py` | 模块初始化 |
| `src/infrastructure/mysql_client.py` | MySQL 连接客户端 |
| `test/infrastructure/__init__.py` | 测试目录 |
| `test/infrastructure/test_mysql_client.py` | 单元测试 |

## 技术规格

### 配置项扩展

```python
# src/api/config.py 新增配置
class APIConfig(BaseModel):
    # ... 现有配置 ...

    # MySQL 配置
    MYSQL_HOST: str = Field(default="localhost", description="MySQL 主机")
    MYSQL_PORT: int = Field(default=3306, description="MySQL 端口")
    MYSQL_USER: str = Field(default="root", description="MySQL 用户名")
    MYSQL_PASSWORD: str = Field(default="", description="MySQL 密码")
    MYSQL_DATABASE: str = Field(default="outdoor_planner", description="数据库名")
    MYSQL_POOL_SIZE: int = Field(default=5, description="连接池大小")
```

### 接口定义

```python
# src/infrastructure/mysql_client.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from contextlib import contextmanager
from typing import Generator


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


class MySQLClient:
    """MySQL 数据库客户端"""

    def __init__(self, config: "APIConfig") -> None:
        """初始化数据库连接"""
        pass

    @contextmanager
    def get_session(self) -> Generator:
        """获取数据库会话（上下文管理器）"""
        pass

    def check_connection(self) -> bool:
        """检查数据库连接是否正常"""
        pass

    def close(self) -> None:
        """关闭所有连接"""
        pass


# 全局实例
mysql_client: MySQLClient | None = None


def get_mysql_client() -> MySQLClient:
    """获取全局 MySQL 客户端实例"""
    pass


def init_mysql_client(config: "APIConfig") -> MySQLClient:
    """初始化全局 MySQL 客户端"""
    pass
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| SQLAlchemy | 需新增依赖 | 待安装 |
| PyMySQL | 需新增依赖 | 待安装 |
| APIConfig | 已存在 | 可用 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/infrastructure/test_mysql_client.py
import pytest
from unittest.mock import patch, MagicMock


class TestMySQLClient:
    """MySQL 客户端测试"""

    def test_init_with_config(self):
        """测试使用配置初始化"""
        # arrange
        # act
        # assert
        pass

    def test_check_connection_success(self):
        """测试连接检查成功"""
        pass

    def test_check_connection_failure(self):
        """测试连接检查失败"""
        pass

    def test_get_session_context_manager(self):
        """测试会话上下文管理器"""
        pass

    def test_close_connections(self):
        """测试关闭连接"""
        pass
```

**测试用例清单**：
- [ ] 配置初始化成功
- [ ] 连接检查成功/失败
- [ ] 会话上下文管理器正常工作
- [ ] 连接池正确关闭
- [ ] 环境变量加载正确

### Step 2: 实现功能

1. 扩展 `src/api/config.py` 添加 MySQL 配置项
2. 创建 `src/infrastructure/mysql_client.py`
3. 实现连接池管理
4. 实现会话上下文管理器

### Step 3: 验证通过

```bash
# 运行测试
pytest test/infrastructure/test_mysql_client.py -v

# 代码检查
ruff check src/infrastructure/mysql_client.py
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
| `src/api/config.py:132-188` | 配置加载模式（from_env） |
| `src/api/config.py:14-23` | Pydantic 配置类模式 |

### 相关文档

- [ITERATION_AUTH_PLAN.md - 4.2 MySQL 表结构](../ITERATION_AUTH_PLAN.md#42-mysql-表结构)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)

## 注意事项

1. **连接池**: 使用 SQLAlchemy 的连接池，避免频繁创建连接
2. **环境变量**: MySQL 配置应从环境变量加载，支持 Docker 部署
3. **异步注意**: 当前项目使用同步 FastAPI，暂不需要异步数据库支持
4. **错误处理**: 连接失败时应抛出明确异常，便于调试
