# TASK-009 认证服务

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 1.5 天 |
| 前置任务 | TASK-003, TASK-004, TASK-005, TASK-008 |
| 后继任务 | TASK-010 |

## 任务目标

实现完整的认证服务，支持用户名注册/登录、手机号注册/登录、密码重置、手机绑定等功能。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/services/auth_service.py` | 新建，认证服务 |
| `src/services/__init__.py` | 扩展，导出认证服务 |
| `src/schemas/auth.py` | 新建，认证相关 Pydantic 模型 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/infrastructure/jwt_handler.py` | 由 TASK-003 负责 |
| `src/infrastructure/password_hasher.py` | 由 TASK-004 负责 |
| `src/repositories/user_repo.py` | 由 TASK-005 负责 |
| `src/services/sms_service.py` | 由 TASK-008 负责 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/services/auth_service.py` | 认证服务 |
| `src/schemas/auth.py` | 认证 Pydantic 模型 |
| `test/services/test_auth_service.py` | 单元测试 |

## 技术规格

### Pydantic 模型

```python
# src/schemas/auth.py
from pydantic import BaseModel, Field
from typing import Optional


class UsernameRegisterRequest(BaseModel):
    """用户名注册请求"""
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    password: str = Field(..., min_length=6, max_length=32)


class UsernameLoginRequest(BaseModel):
    """用户名登录请求"""
    username: str
    password: str


class PhoneRegisterRequest(BaseModel):
    """手机号注册请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=6, max_length=6)
    password: Optional[str] = Field(None, min_length=6, max_length=32)
    username: Optional[str] = Field(None, min_length=3, max_length=20)


class PhoneLoginRequest(BaseModel):
    """手机号登录请求"""
    phone: str
    code: str = Field(..., min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    phone: str
    code: str
    new_password: str = Field(..., min_length=6, max_length=32)


class BindPhoneRequest(BaseModel):
    """绑定手机请求"""
    phone: str
    code: str


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
```

### 接口定义

```python
# src/services/auth_service.py
from dataclasses import dataclass
from src.repositories.user_repo import UserRepository
from src.services.sms_service import SmsService
from src.infrastructure.jwt_handler import JWTHandler
from src.infrastructure.password_hasher import PasswordHasher
from src.schemas.user import UserResponse, UserCreate


@dataclass
class LoginResult:
    """登录结果"""
    success: bool
    user: UserResponse | None = None
    token: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class AuthService:
    """认证服务"""

    def __init__(
        self,
        user_repo: UserRepository,
        sms_service: SmsService,
        jwt_handler: JWTHandler,
        password_hasher: PasswordHasher
    ) -> None:
        pass

    # ===== 注册 =====

    def register_by_username(self, username: str, password: str) -> tuple[UserResponse, str] | None:
        """用户名注册

        Returns:
            (用户信息, token) 或 None（用户名已存在）
        """
        pass

    def register_by_phone(
        self,
        phone: str,
        code: str,
        password: str | None = None,
        username: str | None = None
    ) -> tuple[UserResponse, str] | None:
        """手机号注册"""
        pass

    # ===== 登录 =====

    def login_by_username(self, username: str, password: str) -> LoginResult:
        """用户名登录"""
        pass

    def login_by_phone(self, phone: str, code: str) -> LoginResult:
        """手机号登录"""
        pass

    # ===== 密码管理 =====

    def reset_password(self, phone: str, code: str, new_password: str) -> bool:
        """重置密码"""
        pass

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        pass

    # ===== 手机管理 =====

    def bind_phone(self, user_id: int, phone: str, code: str) -> UserResponse | None:
        """绑定手机"""
        pass

    def unbind_phone(self, user_id: int, code: str) -> UserResponse | None:
        """解绑手机"""
        pass

    # ===== 辅助方法 =====

    def get_user_by_id(self, user_id: int) -> UserResponse | None:
        """根据 ID 获取用户"""
        pass

    def validate_token(self, token: str) -> dict | None:
        """验证 Token"""
        pass
```

### 业务流程

```python
# 用户名注册流程
def register_by_username(self, username: str, password: str):
    # 1. 检查用户名是否存在
    if self.user_repo.exists_by_username(username):
        return None  # 用户名已存在

    # 2. 加密密码
    password_hash = self.password_hasher.hash_password(password)

    # 3. 创建用户
    user = self.user_repo.create(
        UserCreate(username=username, password=password),
        password_hash=password_hash
    )

    # 4. 签发 Token
    token = self.jwt_handler.create_token(user.id, user.username, user.role)

    return (UserResponse.model_validate(user), token)


# 手机号登录流程
def login_by_phone(self, phone: str, code: str) -> LoginResult:
    # 1. 验证验证码
    if not self.sms_service.verify_code(phone, code, "login"):
        return LoginResult(success=False, error_code="INVALID_CODE", error_message="验证码错误")

    # 2. 查找用户
    user = self.user_repo.get_by_phone(phone)
    if not user:
        return LoginResult(success=False, error_code="PHONE_NOT_REGISTERED", error_message="手机号未注册")

    # 3. 检查状态
    if user.status != "active":
        return LoginResult(success=False, error_code="ACCOUNT_DISABLED", error_message="账号已被禁用")

    # 4. 更新登录时间
    self.user_repo.update_last_login(user.id)

    # 5. 签发 Token
    token = self.jwt_handler.create_token(user.id, user.username, user.role)

    return LoginResult(
        success=True,
        user=UserResponse.model_validate(user),
        token=token
    )
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| UserRepository | TASK-005 | 待完成 |
| SmsService | TASK-008 | 待完成 |
| JWTHandler | TASK-003 | 待完成 |
| PasswordHasher | TASK-004 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/services/test_auth_service.py
import pytest
from unittest.mock import MagicMock


class TestAuthService:
    """认证服务测试"""

    # 注册测试
    def test_register_by_username_success(self):
        """测试用户名注册成功"""
        pass

    def test_register_by_username_duplicate(self):
        """测试用户名已存在"""
        pass

    def test_register_by_phone_success(self):
        """测试手机号注册成功"""
        pass

    def test_register_by_phone_invalid_code(self):
        """测试手机号注册验证码错误"""
        pass

    # 登录测试
    def test_login_by_username_success(self):
        """测试用户名登录成功"""
        pass

    def test_login_by_username_wrong_password(self):
        """测试用户名登录密码错误"""
        pass

    def test_login_by_phone_success(self):
        """测试手机号登录成功"""
        pass

    def test_login_by_phone_invalid_code(self):
        """测试手机号登录验证码错误"""
        pass

    # 密码测试
    def test_reset_password_success(self):
        """测试重置密码成功"""
        pass

    def test_change_password_success(self):
        """测试修改密码成功"""
        pass

    # 手机管理测试
    def test_bind_phone_success(self):
        """测试绑定手机成功"""
        pass

    def test_bind_phone_already_bound(self):
        """测试手机号已被绑定"""
        pass
```

**测试用例清单**：
- [ ] 用户名注册成功
- [ ] 用户名注册重复失败
- [ ] 手机号注册成功
- [ ] 手机号注册验证码错误失败
- [ ] 用户名登录成功
- [ ] 用户名登录密码错误失败
- [ ] 手机号登录成功
- [ ] 手机号登录验证码错误失败
- [ ] 重置密码成功
- [ ] 绑定手机成功
- [ ] 手机号已被绑定失败

### Step 2: 实现功能

1. 创建 `src/schemas/auth.py`
2. 创建 `src/services/auth_service.py`
3. 实现所有认证方法

### Step 3: 验证通过

```bash
pytest test/services/test_auth_service.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）
- [ ] 无破坏性变更

## 参考资源

### 相关文档

- [ITERATION_AUTH_PLAN.md - 3.4 接口详情](../ITERATION_AUTH_PLAN.md#34-接口详情)

## 注意事项

1. **密码安全**: 使用 bcrypt 加密，永不明文存储
2. **Token 有效期**: 24 小时，可配置
3. **手机号唯一**: 绑定时检查是否已被其他用户使用
4. **软删除用户**: 禁止登录
