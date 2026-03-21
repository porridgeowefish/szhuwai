# TASK-010 认证 API 路由

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 1 天 |
| 前置任务 | TASK-009 |
| 后继任务 | TASK-012 |

## 任务目标

实现认证相关的 API 路由，提供 RESTful 接口供前端调用。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/api/routes/auth.py` | 新建，认证路由 |
| `src/api/routes/sms.py` | 新建，短信路由 |
| `src/api/routes/__init__.py` | 扩展，导出新路由 |
| `main.py` | 扩展，注册新路由 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/services/auth_service.py` | 由 TASK-009 负责 |
| `src/services/sms_service.py` | 由 TASK-008 负责 |
| 现有 `src/api/routes/plan.py` 等 | 保持现有 API 不变 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/api/routes/auth.py` | 认证 API 路由 |
| `src/api/routes/sms.py` | 短信 API 路由 |
| `test/api/routes/test_auth.py` | API 测试 |

## 技术规格

### 路由定义

```python
# src/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()


# ===== 公开接口 =====

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: UsernameRegisterRequest):
    """用户名注册"""
    pass


@router.post("/login")
async def login(request: UsernameLoginRequest):
    """用户名登录"""
    pass


@router.post("/sms/register")
async def sms_register(request: PhoneRegisterRequest):
    """手机号注册"""
    pass


@router.post("/sms/login")
async def sms_login(request: PhoneLoginRequest):
    """手机号登录"""
    pass


@router.post("/password/reset")
async def reset_password(request: ResetPasswordRequest):
    """重置密码"""
    pass


# ===== 需要认证的接口 =====

@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户信息"""
    pass


@router.post("/phone/bind")
async def bind_phone(request: BindPhoneRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """绑定手机"""
    pass


@router.post("/phone/unbind")
async def unbind_phone(request: UnbindPhoneRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """解绑手机"""
    pass
```

```python
# src/api/routes/sms.py
from fastapi import APIRouter

router = APIRouter(prefix="/auth/sms", tags=["短信"])


@router.post("/send")
async def send_sms(request: SmsSendRequest):
    """发送短信验证码"""
    pass
```

### 响应格式

```python
# 统一响应格式
class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T | None = None


# 示例：登录成功响应
{
    "code": 200,
    "message": "登录成功",
    "data": {
        "accessToken": "eyJhbGciOiJIUzI1NiIs...",
        "tokenType": "Bearer",
        "expiresIn": 86400,
        "user": {
            "id": 1,
            "username": "hiker001",
            "phone": "138****1234",
            "role": "user"
        }
    }
}


# 示例：错误响应
{
    "code": 401001,
    "message": "用户名或密码错误",
    "data": null
}
```

### main.py 集成

```python
# main.py 新增
from src.api.routes import (
    # ... 现有路由 ...
    auth_router,
    sms_router
)

# 注册路由
app.include_router(auth_router, prefix=f"/api/{API_VERSION}")
app.include_router(sms_router, prefix=f"/api/{API_VERSION}")
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| AuthService | TASK-009 | 待完成 |
| SmsService | TASK-008 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/api/routes/test_auth.py
import pytest
from fastapi.testclient import TestClient


class TestAuthRoutes:
    """认证 API 测试"""

    def test_register_success(self, client: TestClient):
        """测试注册成功"""
        pass

    def test_register_duplicate_username(self, client: TestClient):
        """测试用户名重复"""
        pass

    def test_login_success(self, client: TestClient):
        """测试登录成功"""
        pass

    def test_login_wrong_password(self, client: TestClient):
        """测试密码错误"""
        pass

    def test_get_current_user(self, client: TestClient, auth_header: dict):
        """测试获取当前用户"""
        pass

    def test_get_current_user_unauthorized(self, client: TestClient):
        """测试未授权访问"""
        pass


class TestSmsRoutes:
    """短信 API 测试"""

    def test_send_sms_success(self, client: TestClient):
        """测试发送成功"""
        pass

    def test_send_sms_rate_limited(self, client: TestClient):
        """测试频率限制"""
        pass
```

**测试用例清单**：
- [ ] POST /auth/register 成功
- [ ] POST /auth/register 用户名重复失败
- [ ] POST /auth/login 成功
- [ ] POST /auth/login 密码错误失败
- [ ] POST /auth/sms/send 成功
- [ ] POST /auth/sms/send 频率限制失败
- [ ] POST /auth/sms/register 成功
- [ ] POST /auth/sms/login 成功
- [ ] GET /auth/me 成功
- [ ] GET /auth/me 未授权失败
- [ ] POST /auth/phone/bind 成功

### Step 2: 实现功能

1. 创建 `src/api/routes/auth.py`
2. 创建 `src/api/routes/sms.py`
3. 更新 `src/api/routes/__init__.py`
4. 更新 `main.py` 注册路由

### Step 3: 验证通过

```bash
pytest test/api/routes/test_auth.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）
- [ ] API 文档正确生成（/docs）

## 参考资源

### 现有代码参考

| 文件 | 参考内容 |
|------|----------|
| `src/api/routes/track.py` | 路由定义模式 |
| `src/api/routes/plan.py` | 表单处理模式 |
| `main.py:62-67` | 路由注册方式 |

### 相关文档

- [ITERATION_AUTH_PLAN.md - 3.3 接口列表](../ITERATION_AUTH_PLAN.md#33-接口列表)

## 注意事项

1. **HTTP 状态码**: 遵循 RESTful 规范
2. **错误码**: 使用规划文档中定义的错误码
3. **Bearer Token**: 使用 HTTPBearer 安全方案
4. **响应脱敏**: 用户信息中的手机号需要脱敏
