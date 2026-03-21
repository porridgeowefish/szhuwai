# TASK-011 鉴权中间件

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 0.5 天 |
| 前置任务 | TASK-003 |
| 后继任务 | TASK-012 |

## 任务目标

实现鉴权中间件，为需要认证的 API 提供统一的用户身份验证和权限检查。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/middlewares/__init__.py` | 新建，导出中间件 |
| `src/middlewares/auth.py` | 新建，认证中间件 |
| `src/api/deps.py` | 新建，依赖注入 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/infrastructure/jwt_handler.py` | 由 TASK-003 负责 |
| `main.py` | 由 TASK-010 负责路由集成 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/middlewares/__init__.py` | 中间件模块初始化 |
| `src/middlewares/auth.py` | 认证中间件 |
| `src/api/deps.py` | 依赖注入函数 |
| `test/middlewares/test_auth.py` | 单元测试 |

## 技术规格

### 依赖注入

```python
# src/api/deps.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.infrastructure.jwt_handler import get_jwt_handler, TokenPayload
from src.repositories.user_repo import UserRepository


security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    user_repo: UserRepository = Depends()
) -> "UserResponse":
    """获取当前登录用户

    Raises:
        HTTPException: Token 无效或用户不存在
    """
    token = credentials.credentials

    try:
        payload = get_jwt_handler().verify_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401001, "message": "Token 无效或已过期"}
        )

    user = user_repo.get_by_id(payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401001, "message": "用户不存在"}
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 403001, "message": "账号已被禁用"}
        )

    return UserResponse.model_validate(user)


async def get_current_active_user(
    current_user: Annotated["UserResponse", Depends(get_current_user)]
) -> "UserResponse":
    """获取当前活跃用户（别名，便于理解）"""
    return current_user


async def get_admin_user(
    current_user: Annotated["UserResponse", Depends(get_current_user)]
) -> "UserResponse":
    """获取管理员用户

    Raises:
        HTTPException: 非管理员
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 403002, "message": "需要管理员权限"}
        )
    return current_user


# 类型别名，简化使用
CurrentUser = Annotated["UserResponse", Depends(get_current_user)]
AdminUser = Annotated["UserResponse", Depends(get_admin_user)]
```

### 中间件（可选）

```python
# src/middlewares/auth.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件（可选，用于全局认证检查）"""

    async def dispatch(self, request: Request, call_next):
        # 对于需要认证的路径进行检查
        # 注意：通常使用依赖注入方式更灵活
        response = await call_next(request)
        return response
```

### 使用示例

```python
# 在路由中使用
from src.api.deps import CurrentUser, AdminUser

@router.get("/me")
async def get_me(user: CurrentUser):
    """获取当前用户信息"""
    return {"code": 200, "data": user}


@router.get("/admin/users")
async def list_users(admin: AdminUser):
    """管理员接口"""
    pass
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| JWTHandler | TASK-003 | 待完成 |
| UserRepository | TASK-005 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/middlewares/test_auth.py
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient


class TestAuthDeps:
    """认证依赖测试"""

    def test_get_current_user_success(self):
        """测试获取当前用户成功"""
        pass

    def test_get_current_user_invalid_token(self):
        """测试无效 Token"""
        pass

    def test_get_current_user_expired_token(self):
        """测试过期 Token"""
        pass

    def test_get_current_user_disabled(self):
        """测试已禁用用户"""
        pass

    def test_get_admin_user_success(self):
        """测试管理员权限检查成功"""
        pass

    def test_get_admin_user_forbidden(self):
        """测试管理员权限检查失败"""
        pass
```

**测试用例清单**：
- [ ] 获取当前用户成功
- [ ] 无效 Token 返回 401
- [ ] 过期 Token 返回 401
- [ ] 用户不存在返回 401
- [ ] 用户已禁用返回 403
- [ ] 管理员检查成功
- [ ] 非管理员返回 403

### Step 2: 实现功能

1. 创建 `src/api/deps.py`
2. 实现 `get_current_user` 依赖
3. 实现 `get_admin_user` 依赖
4. 创建类型别名

### Step 3: 验证通过

```bash
pytest test/middlewares/test_auth.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）
- [ ] 依赖注入可复用

## 参考资源

### 现有代码参考

| 文件 | 参考内容 |
|------|----------|
| 无 | 本任务为独立新模块 |

### 相关文档

- [FastAPI 依赖注入](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [ITERATION_AUTH_PLAN.md - 5.2 模块划分](../ITERATION_AUTH_PLAN.md#52-模块划分)

## 注意事项

1. **依赖注入**: 优先使用 FastAPI 的 Depends 方式，更灵活
2. **错误格式**: 使用统一的错误码格式
3. **类型别名**: 使用 Annotated 简化路由函数签名
4. **性能**: 避免在每个请求中重复创建 Repository 实例
