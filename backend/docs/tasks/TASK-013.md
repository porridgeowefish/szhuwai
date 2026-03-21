# TASK-013 额度数据模型与仓库

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 0.5 天 |
| 前置任务 | TASK-001（MySQL 连接） |
| 后继任务 | TASK-014 |

## 任务目标

实现额度使用数据模型和数据访问仓库，支持用户每日使用额度的记录和查询。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/models/quota_usage.py` | 新建，额度 ORM 模型 |
| `src/repositories/quota_repo.py` | 新建，额度仓库 |
| `src/schemas/quota.py` | 新建，额度 Pydantic 模型 |
| `src/models/__init__.py` | 扩展，导出新模型 |
| `src/repositories/__init__.py` | 扩展，导出新仓库 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/infrastructure/mysql_client.py` | 由 TASK-001 负责 |
| `src/models/user.py` | 由 TASK-005 负责 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/models/quota_usage.py` | 额度 ORM 模型 |
| `src/repositories/quota_repo.py` | 额度仓库 |
| `src/schemas/quota.py` | 额度 Pydantic 模型 |
| `test/repositories/test_quota_repo.py` | 单元测试 |

## 技术规格

### ORM 模型

```python
# src/models/quota_usage.py
from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.mysql_client import Base


class QuotaUsage(Base):
    """额度使用表"""
    __tablename__ = "quota_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uk_user_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联
    user: Mapped["User"] = relationship()
```

### Pydantic 模型

```python
# src/schemas/quota.py
from datetime import date, datetime
from pydantic import BaseModel, Field


class QuotaInfo(BaseModel):
    """额度信息"""
    used: int = Field(..., description="已使用次数")
    total: int = Field(..., description="总额度")
    remaining: int = Field(..., description="剩余额度")
    reset_at: datetime = Field(..., description="重置时间")

    @property
    def is_unlimited(self) -> bool:
        """是否无限制（管理员）"""
        return self.remaining == -1


class QuotaResponse(BaseModel):
    """额度查询响应"""
    code: int = 200
    message: str = "success"
    data: QuotaInfo
```

### Repository 接口

```python
# src/repositories/quota_repo.py
from datetime import date
from sqlalchemy.orm import Session
from src.models.quota_usage import QuotaUsage


class QuotaRepository:
    """额度数据仓库"""

    # 默认每日额度
    DEFAULT_DAILY_QUOTA = 2

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(self, user_id: int, usage_date: date | None = None) -> QuotaUsage:
        """获取或创建当日额度记录"""
        pass

    def get_usage(self, user_id: int, usage_date: date | None = None) -> int:
        """获取当日已使用次数"""
        pass

    def increment_usage(self, user_id: int, usage_date: date | None = None) -> int:
        """增加使用次数，返回增加后的次数"""
        pass

    def check_quota(self, user_id: int, max_count: int = DEFAULT_DAILY_QUOTA) -> tuple[bool, int]:
        """检查是否有剩余额度

        Returns:
            (是否有剩余, 剩余次数)
        """
        pass

    def reset_if_new_day(self, user_id: int) -> bool:
        """如果是新的一天，创建新的记录

        Returns:
            是否创建了新记录
        """
        pass
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| MySQLClient | TASK-001 | 待完成 |
| User 模型 | TASK-005 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/repositories/test_quota_repo.py
import pytest
from datetime import date, timedelta


class TestQuotaRepository:
    """额度仓库测试"""

    def test_get_or_create_new(self, db_session):
        """测试创建新记录"""
        pass

    def test_get_or_create_existing(self, db_session):
        """测试获取已存在记录"""
        pass

    def test_get_usage_zero(self, db_session):
        """测试获取初始使用次数为0"""
        pass

    def test_increment_usage(self, db_session):
        """测试增加使用次数"""
        pass

    def test_check_quota_available(self, db_session):
        """测试检查额度充足"""
        pass

    def test_check_quota_exhausted(self, db_session):
        """测试检查额度耗尽"""
        pass

    def test_usage_by_date(self, db_session):
        """测试按日期隔离使用记录"""
        pass

    def test_unique_constraint(self, db_session):
        """测试用户+日期唯一约束"""
        pass
```

**测试用例清单**：
- [ ] 创建新额度记录
- [ ] 获取已存在记录
- [ ] 初始使用次数为 0
- [ ] 增加使用次数
- [ ] 检查额度充足
- [ ] 检查额度耗尽
- [ ] 按日期隔离
- [ ] 唯一约束生效

### Step 2: 实现功能

1. 创建 ORM 模型
2. 创建 Pydantic 模型
3. 创建 Repository 类

### Step 3: 验证通过

```bash
pytest test/repositories/test_quota_repo.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）

## 参考资源

### 相关文档

- [ITERATION_AUTH_PLAN.md - 4.2.4 quota_usage 表](../ITERATION_AUTH_PLAN.md#424-quota_usage额度使用表)
- [ITERATION_AUTH_PLAN.md - 4.4 额度配置](../ITERATION_AUTH_PLAN.md#44-数据字典)

## 注意事项

1. **日期隔离**: 使用日期字段隔离每天的额度
2. **唯一约束**: user_id + usage_date 唯一
3. **原子操作**: increment_usage 需要原子性保证
4. **0点重置**: 通过日期字段自然实现
