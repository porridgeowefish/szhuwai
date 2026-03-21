# TASK-003 JWT 认证工具类

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 预估工时 | 0.5 天 |
| 前置任务 | 无 |
| 后继任务 | TASK-009, TASK-011 |

## 任务目标

实现 JWT Token 签发和验证工具类，支持用户认证和会话管理。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/infrastructure/jwt_handler.py` | 新建，JWT 工具类 |
| `src/infrastructure/__init__.py` | 扩展，导出 JWT 工具 |
| `src/api/config.py` | 扩展，添加 JWT 配置项 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `main.py` | 入口文件，其他任务负责集成 |
| 现有 `src/api/routes/*.py` | 保持现有 API 不变 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/infrastructure/jwt_handler.py` | JWT 工具类 |
| `test/infrastructure/test_jwt_handler.py` | 单元测试 |

## 技术规格

### 配置项扩展

```python
# src/api/config.py 新增配置
class APIConfig(BaseModel):
    # ... 现有配置 ...

    # JWT 配置
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="JWT 签名密钥"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT 签名算法"
    )
    JWT_EXPIRE_SECONDS: int = Field(
        default=86400,  # 24小时
        description="Token 有效期（秒）"
    )
```

### 接口定义

```python
# src/infrastructure/jwt_handler.py
from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass


@dataclass
class TokenPayload:
    """Token 载荷数据"""
    user_id: int
    username: str | None
    role: str
    exp: datetime
    iat: datetime


class JWTHandler:
    """JWT Token 处理器"""

    def __init__(self, config: "APIConfig") -> None:
        """初始化 JWT 处理器"""
        pass

    def create_token(
        self,
        user_id: int,
        username: str | None,
        role: str = "user"
    ) -> str:
        """签发 JWT Token"""
        pass

    def verify_token(self, token: str) -> TokenPayload:
        """验证 JWT Token，返回载荷"""
        pass

    def decode_token(self, token: str) -> dict[str, Any]:
        """解码 JWT Token（不验证）"""
        pass

    def get_expired_at(self, token: str) -> datetime:
        """获取 Token 过期时间"""
        pass


# 全局实例
jwt_handler: JWTHandler | None = None


def get_jwt_handler() -> JWTHandler:
    """获取全局 JWT 处理器实例"""
    pass


def init_jwt_handler(config: "APIConfig") -> JWTHandler:
    """初始化全局 JWT 处理器"""
    pass
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| python-jose[cryptography] | 需新增依赖 | 待安装 |
| APIConfig | 已存在 | 可用 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/infrastructure/test_jwt_handler.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch


class TestJWTHandler:
    """JWT 处理器测试"""

    def test_create_token(self):
        """测试创建 Token"""
        pass

    def test_verify_token_success(self):
        """测试验证有效 Token"""
        pass

    def test_verify_token_expired(self):
        """测试验证过期 Token"""
        pass

    def test_verify_token_invalid(self):
        """测试验证无效 Token"""
        pass

    def test_verify_token_tampered(self):
        """测试验证被篡改的 Token"""
        pass

    def test_decode_token(self):
        """测试解码 Token"""
        pass

    def test_get_expired_at(self):
        """测试获取过期时间"""
        pass
```

**测试用例清单**：
- [ ] 创建 Token 成功
- [ ] 验证有效 Token 成功
- [ ] 验证过期 Token 抛出异常
- [ ] 验证无效 Token 抛出异常
- [ ] 验证被篡改 Token 抛出异常
- [ ] 解码 Token 正确
- [ ] 过期时间计算正确

### Step 2: 实现功能

1. 扩展 `src/api/config.py` 添加 JWT 配置项
2. 创建 `src/infrastructure/jwt_handler.py`
3. 实现 Token 签发和验证

### Step 3: 验证通过

```bash
# 运行测试
pytest test/infrastructure/test_jwt_handler.py -v

# 代码检查
ruff check src/infrastructure/jwt_handler.py
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
| `src/api/config.py:14-23` | Pydantic 配置类模式 |

### 相关文档

- [ITERATION_AUTH_PLAN.md - 5.6 配置项](../ITERATION_AUTH_PLAN.md#56-配置项)
- [python-jose 文档](https://python-jose.readthedocs.io/)

## 注意事项

1. **密钥安全**: 生产环境必须使用强密钥，从环境变量加载
2. **过期处理**: Token 过期应抛出明确异常
3. **时区处理**: 使用 UTC 时间
4. **算法选择**: 默认 HS256，足够满足需求
