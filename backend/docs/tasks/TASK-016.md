# TASK-016 报告服务

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 0.5 天 |
| 前置任务 | TASK-015 |
| 后继任务 | TASK-018 |

## 任务目标

实现报告业务服务，封装报告的 CRUD 逻辑，提供权限校验。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/services/report_service.py` | 新建，报告服务 |
| `src/services/__init__.py` | 扩展，导出报告服务 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/repositories/report_repo.py` | 由 TASK-015 负责 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/services/report_service.py` | 报告服务 |
| `test/services/test_report_service.py` | 单元测试 |

## 技术规格

### 接口定义

```python
# src/services/report_service.py
from src.repositories.report_repo import ReportRepository
from src.schemas.report import ReportCreate, ReportDetail, ReportListItem


class ReportService:
    """报告业务服务"""

    def __init__(self, report_repo: ReportRepository) -> None:
        self.report_repo = report_repo

    def create(self, user_id: int, plan_data: dict) -> str:
        """创建报告

        Args:
            user_id: 用户 ID
            plan_data: 完整的计划数据（OutdoorActivityPlan）

        Returns:
            报告 ID
        """
        pass

    def get_by_id(self, report_id: str, user_id: int) -> ReportDetail | None:
        """获取报告详情（鉴权）

        只能获取自己的报告

        Args:
            report_id: 报告 ID
            user_id: 当前用户 ID

        Returns:
            报告详情或 None
        """
        pass

    def list_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[ReportListItem], dict]:
        """获取用户报告列表

        Returns:
            (报告列表, 分页信息)
        """
        pass

    def delete(self, report_id: str, user_id: int) -> bool:
        """删除报告（鉴权）

        只能删除自己的报告

        Returns:
            是否删除成功
        """
        pass

    def _extract_report_info(self, plan_data: dict) -> tuple[str, str, str]:
        """从计划数据中提取报告信息

        Returns:
            (plan_name, trip_date, overall_rating)
        """
        pass
```

### 业务逻辑

```python
def create(self, user_id: int, plan_data: dict) -> str:
    """创建报告"""
    # 1. 提取报告信息
    plan_name = plan_data.get("plan_name", "未命名计划")
    trip_date = plan_data.get("trip_date", "")
    overall_rating = plan_data.get("overall_rating", "")

    # 2. 创建报告
    report_create = ReportCreate(
        user_id=user_id,
        plan_name=plan_name,
        trip_date=trip_date,
        overall_rating=overall_rating,
        content=plan_data
    )

    return self.report_repo.create(report_create)


def get_by_id(self, report_id: str, user_id: int) -> ReportDetail | None:
    """获取报告详情（鉴权）"""
    report = self.report_repo.get_by_id(report_id, user_id=user_id)
    if report and report.user_id != user_id:
        return None  # 不是自己的报告
    return report


def delete(self, report_id: str, user_id: int) -> bool:
    """删除报告（鉴权）"""
    # 先检查报告是否存在且属于该用户
    report = self.report_repo.get_by_id(report_id, user_id=user_id)
    if not report:
        return False

    return self.report_repo.delete(report_id, user_id)
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| ReportRepository | TASK-015 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/services/test_report_service.py
import pytest
from unittest.mock import MagicMock


class TestReportService:
    """报告服务测试"""

    def test_create_report(self):
        """测试创建报告"""
        pass

    def test_get_by_id_success(self):
        """测试获取自己的报告成功"""
        pass

    def test_get_by_id_not_owner(self):
        """测试获取他人报告返回 None"""
        pass

    def test_list_by_user(self):
        """测试获取报告列表"""
        pass

    def test_delete_success(self):
        """测试删除自己的报告成功"""
        pass

    def test_delete_not_owner(self):
        """测试删除他人报告失败"""
        pass

    def test_delete_not_found(self):
        """测试删除不存在的报告失败"""
        pass
```

**测试用例清单**：
- [ ] 创建报告成功
- [ ] 获取自己的报告成功
- [ ] 获取他人报告返回 None
- [ ] 获取报告列表正确
- [ ] 删除自己的报告成功
- [ ] 删除他人报告失败
- [ ] 删除不存在报告失败

### Step 2: 实现功能

1. 创建 `src/services/report_service.py`
2. 实现 CRUD 逻辑

### Step 3: 验证通过

```bash
pytest test/services/test_report_service.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）

## 参考资源

### 相关文档

- [ITERATION_AUTH_PLAN.md - 5.5 核心模块接口 - report_service](../ITERATION_AUTH_PLAN.md#55-核心模块接口)

## 注意事项

1. **权限校验**: 所有操作都需要验证用户身份
2. **软删除**: delete 方法调用仓库的软删除
3. **数据提取**: 从 plan_data 中提取 plan_name 等字段
