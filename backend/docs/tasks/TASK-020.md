# TASK-020 完整流程集成测试

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P2 |
| 预估工时 | 1 天 |
| 前置任务 | TASK-012, TASK-017, TASK-018, TASK-019 |
| 后继任务 | 无 |

## 任务目标

对整个认证、额度、报告系统进行端到端集成测试，验证完整业务流程。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `test/integration/test_full_flow.py` | 新建，完整流程测试 |
| `test/conftest.py` | 扩展，添加更多 fixtures |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/` 下所有文件 | 集成测试不应修改源码 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `test/integration/test_full_flow.py` | 完整流程集成测试 |

## 技术规格

### 测试场景

```python
# test/integration/test_full_flow.py
import pytest
from fastapi.testclient import TestClient


class TestFullFlow:
    """完整业务流程集成测试"""

    # ===== 用户注册到生成计划完整流程 =====

    def test_full_user_journey(self, client: TestClient, mock_sms):
        """测试完整的用户旅程"""
        # 1. 用户名注册
        # 2. 登录获取 Token
        # 3. 查看额度（初始 2 次）
        # 4. 生成计划
        # 5. 查看额度（剩余 1 次）
        # 6. 查看报告列表
        # 7. 查看报告详情
        # 8. 删除报告
        pass

    # ===== 手机号用户流程 =====

    def test_phone_user_journey(self, client: TestClient, mock_sms):
        """测试手机号用户完整流程"""
        # 1. 发送验证码
        # 2. 手机号注册
        # 3. 手机号登录
        # 4. 生成计划
        pass

    # ===== 额度限制流程 =====

    def test_quota_limit_flow(self, client: TestClient, auth_header: dict):
        """测试额度限制流程"""
        # 1. 查看额度（2 次）
        # 2. 生成计划（剩余 1 次）
        # 3. 生成计划（剩余 0 次）
        # 4. 生成计划失败（额度耗尽）
        pass

    # ===== 管理员流程 =====

    def test_admin_journey(self, client: TestClient, admin_auth_header: dict):
        """测试管理员完整流程"""
        # 1. 查看用户列表
        # 2. 禁用用户
        # 3. 被禁用用户无法登录
        # 4. 启用用户
        # 5. 管理员生成计划（无额度限制）
        pass

    # ===== 报告管理流程 =====

    def test_report_management_flow(self, client: TestClient, auth_header: dict):
        """测试报告管理流程"""
        # 1. 生成计划创建报告
        # 2. 查看报告列表
        # 3. 查看报告详情
        # 4. 删除报告
        # 5. 报告列表不再显示
        pass

    # ===== 权限隔离 =====

    def test_user_isolation(self, client: TestClient):
        """测试用户数据隔离"""
        # 1. 用户 A 创建报告
        # 2. 用户 B 无法查看用户 A 的报告
        # 3. 用户 B 无法删除用户 A 的报告
        pass

    # ===== 密码重置流程 =====

    def test_password_reset_flow(self, client: TestClient, mock_sms):
        """测试密码重置流程"""
        # 1. 用户名注册（带手机）
        # 2. 发送验证码
        # 3. 重置密码
        # 4. 新密码登录成功
        pass


class TestErrorScenarios:
    """错误场景测试"""

    def test_invalid_token(self, client: TestClient):
        """测试无效 Token"""
        pass

    def test_expired_token(self, client: TestClient):
        """测试过期 Token"""
        pass

    def test_disabled_user(self, client: TestClient, admin_auth_header: dict):
        """测试已禁用用户"""
        pass

    def test_wrong_password(self, client: TestClient):
        """测试密码错误"""
        pass

    def test_invalid_sms_code(self, client: TestClient):
        """测试验证码错误"""
        pass

    def test_duplicate_username(self, client: TestClient):
        """测试用户名重复"""
        pass

    def test_duplicate_phone(self, client: TestClient, mock_sms):
        """测试手机号重复"""
        pass


class TestRateLimit:
    """频率限制测试"""

    def test_sms_rate_limit(self, client: TestClient):
        """测试短信发送频率限制"""
        pass

    def test_sms_daily_limit(self, client: TestClient):
        """测试短信每日上限"""
        pass
```

### 测试用例清单

#### 完整流程
- [ ] 用户名注册 → 登录 → 查额度 → 生成计划 → 查报告
- [ ] 手机号注册 → 手机登录 → 生成计划
- [ ] 额度限制流程（2次 → 1次 → 0次 → 失败）
- [ ] 管理员流程（用户管理 + 无额度限制）

#### 权限隔离
- [ ] 用户无法查看他人报告
- [ ] 用户无法删除他人报告

#### 错误场景
- [ ] 无效 Token
- [ ] 过期 Token
- [ ] 已禁用用户
- [ ] 密码错误
- [ ] 验证码错误
- [ ] 用户名重复
- [ ] 手机号重复

#### 频率限制
- [ ] 短信发送冷却
- [ ] 短信每日上限

## 实现步骤

### Step 1: 编写测试框架

1. 扩展 `test/conftest.py` 添加更多 fixtures
2. 准备测试数据

### Step 2: 编写测试用例

1. 编写完整流程测试
2. 编写错误场景测试
3. 编写频率限制测试

### Step 3: 验证通过

```bash
# 运行集成测试
pytest test/integration/test_full_flow.py -v

# 运行所有测试
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

1. **测试隔离**: 每个测试用例使用独立数据
2. **Mock 短信**: 使用固定验证码
3. **数据库清理**: 测试后清理数据
4. **并发安全**: 频率限制测试注意并发
