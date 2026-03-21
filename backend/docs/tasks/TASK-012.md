# TASK-012 认证模块集成测试

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P2 |
| 预估工时 | 1 天 |
| 前置任务 | TASK-010, TASK-011 |
| 后继任务 | 无 |

## 任务目标

对认证模块进行端到端集成测试，验证完整业务流程的正确性。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `test/integration/test_auth_flow.py` | 新建，集成测试 |
| `test/conftest.py` | 扩展，添加认证相关 fixtures |
| `test/fixtures/__init__.py` | 新建，测试数据 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/` 下所有文件 | 集成测试不应修改源码 |
| 现有 `test/` 下测试 | 保持现有测试独立 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `test/integration/test_auth_flow.py` | 认证流程集成测试 |
| `test/fixtures/auth_fixtures.py` | 测试数据 fixtures |

## 技术规格

### 测试场景

```python
# test/integration/test_auth_flow.py
import pytest
from fastapi.testclient import TestClient


class TestAuthFlow:
    """认证流程集成测试"""

    # ===== 用户名注册登录流程 =====

    def test_username_register_and_login_flow(self, client: TestClient):
        """测试完整的用户名注册登录流程"""
        # 1. 注册
        # 2. 登录
        # 3. 获取用户信息
        # 4. 验证返回数据正确
        pass

    # ===== 手机号注册登录流程 =====

    def test_phone_register_and_login_flow(self, client: TestClient, mock_sms):
        """测试完整的手机号注册登录流程"""
        # 1. 发送验证码（Mock）
        # 2. 手机号注册
        # 3. 手机号登录
        # 4. 验证返回数据正确
        pass

    # ===== 密码重置流程 =====

    def test_reset_password_flow(self, client: TestClient, mock_sms):
        """测试密码重置流程"""
        # 1. 用户名注册（带手机绑定）
        # 2. 发送验证码
        # 3. 重置密码
        # 4. 用新密码登录成功
        pass

    # ===== 手机绑定流程 =====

    def test_bind_phone_flow(self, client: TestClient, mock_sms):
        """测试手机绑定流程"""
        # 1. 用户名注册（无手机）
        # 2. 发送验证码
        # 3. 绑定手机
        # 4. 验证手机已绑定
        pass

    # ===== 错误场景 =====

    def test_duplicate_username_fails(self, client: TestClient):
        """测试用户名重复注册失败"""
        pass

    def test_duplicate_phone_fails(self, client: TestClient, mock_sms):
        """测试手机号重复注册失败"""
        pass

    def test_login_with_wrong_password_fails(self, client: TestClient):
        """测试密码错误登录失败"""
        pass

    def test_login_with_invalid_code_fails(self, client: TestClient):
        """测试验证码错误登录失败"""
        pass

    def test_access_protected_route_without_token_fails(self, client: TestClient):
        """测试无 Token 访问受保护接口失败"""
        pass

    def test_access_protected_route_with_invalid_token_fails(self, client: TestClient):
        """测试无效 Token 访问受保护接口失败"""
        pass

    # ===== 并发场景 =====

    def test_concurrent_sms_send_rate_limit(self, client: TestClient):
        """测试并发发送验证码的频率限制"""
        pass

    # ===== 边界场景 =====

    def test_token_expiration(self, client: TestClient):
        """测试 Token 过期"""
        pass

    def test_disabled_user_login_fails(self, client: TestClient):
        """测试已禁用用户登录失败"""
        pass
```

### Fixtures 扩展

```python
# test/conftest.py 新增

@pytest.fixture
def client() -> TestClient:
    """测试客户端"""
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_sms(mocker):
    """Mock 短信发送"""
    # 返回固定的验证码
    return mocker.patch(
        "src.services.sms_service.SmsService._send_sms",
        return_value=True
    )


@pytest.fixture
def auth_header(client: TestClient, test_user: dict) -> dict:
    """认证请求头"""
    response = client.post("/api/v1/auth/login", json=test_user)
    token = response.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user() -> dict:
    """测试用户数据"""
    return {
        "username": "testuser001",
        "password": "Test@123456"
    }


@pytest.fixture
def test_phone() -> str:
    """测试手机号"""
    return "13800138000"
```

### 测试用例清单

#### 正向流程
- [ ] 用户名注册 → 登录 → 获取用户信息
- [ ] 手机号注册 → 手机号登录 → 获取用户信息
- [ ] 密码重置 → 新密码登录
- [ ] 手机绑定 → 手机号登录
- [ ] 手机解绑

#### 错误场景
- [ ] 用户名重复注册失败
- [ ] 手机号重复注册失败
- [ ] 密码错误登录失败
- [ ] 验证码错误登录失败
- [ ] 无 Token 访问失败
- [ ] 无效 Token 访问失败
- [ ] 过期 Token 访问失败
- [ ] 已禁用用户登录失败

#### 频率限制
- [ ] 验证码发送冷却限制
- [ ] 每日发送次数限制

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| TASK-010 API 路由 | TASK-010 | 待完成 |
| TASK-011 鉴权中间件 | TASK-011 | 待完成 |
| pytest-mock | 需新增依赖 | 待安装 |

## 实现步骤

### Step 1: 编写测试框架

1. 扩展 `test/conftest.py`
2. 创建测试 fixtures
3. 准备 Mock 策略

### Step 2: 编写测试用例

1. 编写正向流程测试
2. 编写错误场景测试
3. 编写边界场景测试

### Step 3: 验证通过

```bash
# 运行集成测试
pytest test/integration/test_auth_flow.py -v

# 运行所有测试确保无回归
pytest test/ -v
```

## 验收标准

- [ ] 所有集成测试通过
- [ ] 所有现有测试仍通过（无回归）
- [ ] 测试覆盖主要业务流程
- [ ] 测试覆盖错误场景

## 参考资源

### 现有代码参考

| 文件 | 参考内容 |
|------|----------|
| `test/integration/test_workflow.py` | 集成测试模式 |

### 相关文档

- [ITERATION_AUTH_PLAN.md - 2.4 业务流程](../ITERATION_AUTH_PLAN.md#24-业务流程)

## 注意事项

1. **Mock 短信**: 集成测试中 Mock 短信发送，使用固定验证码
2. **测试隔离**: 每个测试用例使用独立的测试数据
3. **数据库清理**: 测试后清理数据，避免污染
4. **并发安全**: 频率限制测试需要考虑并发情况
5. **环境隔离**: 使用测试数据库，不影响开发数据
