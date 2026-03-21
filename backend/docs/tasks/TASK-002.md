# TASK-002 MongoDB 数据库连接

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 预估工时 | 0.5 天 |
| 前置任务 | 无 |
| 后继任务 | TASK-012（报告服务依赖） |

## 任务目标

实现 MongoDB 数据库连接基础设施，用于存储户外活动计划报告的 JSON 数据。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/infrastructure/mongo_client.py` | 新建，MongoDB 连接管理 |
| `src/infrastructure/__init__.py` | 扩展，导出 MongoDB 客户端 |
| `src/api/config.py` | 扩展，添加 MongoDB 配置项 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `main.py` | 入口文件，其他任务负责集成 |
| `src/domain/orchestrator.py` | 保持现有逻辑不变 |
| 现有 `src/schemas/output.py` | 保持现有模型不变 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/infrastructure/mongo_client.py` | MongoDB 连接客户端 |
| `test/infrastructure/test_mongo_client.py` | 单元测试 |

## 技术规格

### 配置项扩展

```python
# src/api/config.py 新增配置
class APIConfig(BaseModel):
    # ... 现有配置 ...

    # MongoDB 配置
    MONGO_HOST: str = Field(default="localhost", description="MongoDB 主机")
    MONGO_PORT: int = Field(default=27017, description="MongoDB 端口")
    MONGO_USER: str = Field(default="", description="MongoDB 用户名")
    MONGO_PASSWORD: str = Field(default="", description="MongoDB 密码")
    MONGO_DATABASE: str = Field(default="outdoor_planner", description="数据库名")
```

### 接口定义

```python
# src/infrastructure/mongo_client.py
from pymongo import MongoClient
from pymongo.database import Database
from typing import Any


class MongoClientWrapper:
    """MongoDB 数据库客户端包装器"""

    def __init__(self, config: "APIConfig") -> None:
        """初始化 MongoDB 连接"""
        pass

    @property
    def db(self) -> Database:
        """获取数据库实例"""
        pass

    def get_collection(self, name: str):
        """获取集合"""
        pass

    def check_connection(self) -> bool:
        """检查数据库连接是否正常"""
        pass

    def close(self) -> None:
        """关闭连接"""
        pass


# 全局实例
mongo_client: MongoClientWrapper | None = None


def get_mongo_client() -> MongoClientWrapper:
    """获取全局 MongoDB 客户端实例"""
    pass


def init_mongo_client(config: "APIConfig") -> MongoClientWrapper:
    """初始化全局 MongoDB 客户端"""
    pass
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| pymongo | 需新增依赖 | 待安装 |
| APIConfig | 已存在 | 可用 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/infrastructure/test_mongo_client.py
import pytest
from unittest.mock import patch, MagicMock


class TestMongoClientWrapper:
    """MongoDB 客户端测试"""

    def test_init_with_config(self):
        """测试使用配置初始化"""
        pass

    def test_check_connection_success(self):
        """测试连接检查成功"""
        pass

    def test_check_connection_failure(self):
        """测试连接检查失败"""
        pass

    def test_get_collection(self):
        """测试获取集合"""
        pass

    def test_close_connection(self):
        """测试关闭连接"""
        pass
```

**测试用例清单**：
- [ ] 配置初始化成功
- [ ] 连接检查成功/失败
- [ ] 获取集合正确
- [ ] 连接正确关闭
- [ ] 支持无认证连接

### Step 2: 实现功能

1. 扩展 `src/api/config.py` 添加 MongoDB 配置项
2. 创建 `src/infrastructure/mongo_client.py`
3. 实现连接管理和集合访问

### Step 3: 验证通过

```bash
# 运行测试
pytest test/infrastructure/test_mongo_client.py -v

# 代码检查
ruff check src/infrastructure/mongo_client.py
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
| `src/api/config.py:132-188` | 配置加载模式 |

### 相关文档

- [ITERATION_AUTH_PLAN.md - 4.3 MongoDB 集合结构](../ITERATION_AUTH_PLAN.md#43-mongodb-集合结构)
- [PyMongo 文档](https://pymongo.readthedocs.io/)

## 注意事项

1. **连接复用**: 使用单例模式，避免重复创建连接
2. **认证可选**: 支持无认证连接（开发环境）
3. **集合初始化**: 暂不需要创建集合，MongoDB 自动创建
4. **索引创建**: 索引由后续任务按需创建
