# TASK-014 额度服务

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 0.5 天 |
| 前置任务 | TASK-005, TASK-013 |
| 后继任务 | TASK-017 |

## 任务目标

实现额度业务服务，提供额度查询、检查和扣减功能，支持管理员无限制额度。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/services/quota_service.py` | 新建，额度服务 |
| `src/services/__init__.py` | 扩展，导出额度服务 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/repositories/quota_repo.py` | 由 TASK-013 负责 |
| `src/repositories/user_repo.py` | 由 TASK-005 负责 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/services/quota_service.py` | 额度服务 |
| `test/services/test_quota_service.py` | 单元测试 |

## 技术规格

### 接口定义

```python
# src/services/quota_service.py
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.repositories.quota_repo import QuotaRepository
from src.repositories.user_repo import UserRepository
from src.schemas.quota import QuotaInfo


@dataclass
class QuotaCheckResult:
    """额度检查结果"""
    has_quota: bool
    remaining: int
    used: int
    message: str | None = None


class QuotaService:
    """额度业务服务"""

    # 默认每日额度
    DEFAULT_DAILY_QUOTA = 2

    def __init__(
        self,
        quota_repo: QuotaRepository,
        user_repo: UserRepository
    ) -> None:
        pass

    def get_quota_info(self, user_id: int) -> QuotaInfo:
        """获取用户额度信息

        管理员返回 remaining=-1 表示无限制
        """
        pass

    def check_quota(self, user_id: int) -> QuotaCheckResult:
        """检查用户是否有剩余额度"""
        pass

    def consume_quota(self, user_id: int) -> bool:
        """消耗一次额度

        Returns:
            是否消耗成功（额度不足时返回 False）
        """
        pass

    def get_reset_time(self) -> datetime:
        """获取下次重置时间（明天 0 点）"""
        pass

    def _is_admin(self, user_id: int) -> bool:
        """检查用户是否为管理员"""
        pass

    def _get_user_role(self, user_id: int) -> str:
        """获取用户角色"""
        pass
```

### 业务逻辑

```python
def get_quota_info(self, user_id: int) -> QuotaInfo:
    """获取用户额度信息"""
    # 1. 获取用户信息
    user = self.user_repo.get_by_id(user_id)
    if not user:
        raise ValueError("用户不存在")

    # 2. 管理员返回无限制
    if user.role == "admin":
        return QuotaInfo(
            used=0,
            total=-1,
            remaining=-1,
            reset_at=self.get_reset_time()
        )

    # 3. 普通用户查询当日使用量
    used = self.quota_repo.get_usage(user_id)
    return QuotaInfo(
        used=used,
        total=self.DEFAULT_DAILY_QUOTA,
        remaining=max(0, self.DEFAULT_DAILY_QUOTA - used),
        reset_at=self.get_reset_time()
    )


def consume_quota(self, user_id: int) -> bool:
    """消耗一次额度"""
    # 1. 检查用户
    user = self.user_repo.get_by_id(user_id)
    if not user:
        return False

    # 2. 管理员无限制
    if user.role == "admin":
        return True

    # 3. 检查额度
    check_result = self.check_quota(user_id)
    if not check_result.has_quota:
        return False

    # 4. 扣减额度
    self.quota_repo.increment_usage(user_id)
    return True
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| QuotaRepository | TASK-013 | 待完成 |
| UserRepository | TASK-005 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/services/test_quota_service.py
import pytest
from unittest.mock import MagicMock


class TestQuotaService:
    """额度服务测试"""

    def test_get_quota_info_normal_user(self):
        """测试普通用户额度信息"""
        pass

    def test_get_quota_info_admin_user(self):
        """测试管理员额度信息（无限制）"""
        pass

    def test_check_quota_available(self):
        """测试检查额度充足"""
        pass

    def test_check_quota_exhausted(self):
        """测试检查额度耗尽"""
        pass

    def test_consume_quota_success(self):
        """测试消耗额度成功"""
        pass

    def test_consume_quota_failed(self):
        """测试消耗额度失败（额度不足）"""
        pass

    def test_consume_quota_admin(self):
        """测试管理员消耗额度（始终成功）"""
        pass

    def test_get_reset_time(self):
        """测试获取重置时间"""
        pass
```

**测试用例清单**：
- [ ] 普通用户额度信息正确
- [ ] 管理员返回无限制（-1）
- [ ] 检查额度充足返回 True
- [ ] 检查额度耗尽返回 False
- [ ] 消耗额度成功
- [ ] 消耗额度失败（额度不足）
- [ ] 管理员消耗始终成功
- [ ] 重置时间为明天 0 点

### Step 2: 实现功能

1. 创建 `src/services/quota_service.py`
2. 实现额度查询、检查、消耗逻辑

### Step 3: 验证通过

```bash
pytest test/services/test_quota_service.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）

## 参考资源

### 相关文档

- [ITERATION_AUTH_PLAN.md - 5.5 核心模块接口 - quota_service](../ITERATION_AUTH_PLAN.md#55-核心模块接口)

## 注意事项

1. **管理员无限制**: 管理员返回 remaining=-1
2. **原子操作**: consume_quota 需要检查+扣减的原子性
3. **重置时间**: 明天 0 点（UTC 或本地时间）
4. **用户不存在**: 抛出异常或返回特定错误
