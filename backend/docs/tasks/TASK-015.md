# TASK-015 报告数据模型与仓库

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 0.5 天 |
| 前置任务 | TASK-002（MongoDB 连接） |
| 后继任务 | TASK-016 |

## 任务目标

实现报告数据模型和数据访问仓库，支持户外活动计划报告的 CRUD 操作。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/models/report.py` | 新建，报告模型（MongoDB） |
| `src/repositories/report_repo.py` | 新建，报告仓库 |
| `src/schemas/report.py` | 新建，报告 Pydantic 模型 |
| `src/models/__init__.py` | 扩展，导出新模型 |
| `src/repositories/__init__.py` | 扩展，导出新仓库 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/infrastructure/mongo_client.py` | 由 TASK-002 负责 |
| `src/schemas/output.py` | 保持现有模型不变 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/models/report.py` | 报告 MongoDB 模型 |
| `src/repositories/report_repo.py` | 报告仓库 |
| `src/schemas/report.py` | 报告 Pydantic 模型 |
| `test/repositories/test_report_repo.py` | 单元测试 |

## 技术规格

### MongoDB 文档模型

```python
# src/models/report.py
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class ReportDocument(BaseModel):
    """报告 MongoDB 文档模型"""
    id: Optional[ObjectId] = Field(None, alias="_id")
    user_id: int = Field(..., description="用户 ID")
    plan_name: str = Field(..., description="计划名称")
    trip_date: str = Field(..., description="出行日期")
    overall_rating: str = Field(..., description="总体评分")
    content: dict[str, Any] = Field(..., description="完整的计划内容")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(None, description="软删除时间")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
```

### Pydantic 模型

```python
# src/schemas/report.py
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class ReportListItem(BaseModel):
    """报告列表项"""
    id: str = Field(..., description="报告 ID")
    plan_name: str = Field(..., description="计划名称")
    trip_date: str = Field(..., description="出行日期")
    overall_rating: str = Field(..., description="总体评分")
    created_at: datetime = Field(..., description="创建时间")


class ReportDetail(ReportListItem):
    """报告详情"""
    user_id: int = Field(..., description="用户 ID")
    content: dict[str, Any] = Field(..., description="完整的计划内容")


class ReportCreate(BaseModel):
    """创建报告请求"""
    user_id: int
    plan_name: str
    trip_date: str
    overall_rating: str
    content: dict[str, Any]


class ReportListResponse(BaseModel):
    """报告列表响应"""
    list: list[ReportListItem]
    pagination: dict
```

### Repository 接口

```python
# src/repositories/report_repo.py
from datetime import datetime
from typing import Optional
from pymongo.database import Database
from pymongo import ASCENDING, DESCENDING
from src.models.report import ReportDocument
from src.schemas.report import ReportCreate, ReportListItem, ReportDetail


class ReportRepository:
    """报告数据仓库"""

    COLLECTION_NAME = "reports"

    def __init__(self, db: Database) -> None:
        self.collection = db[self.COLLECTION_NAME]

    def create(self, data: ReportCreate) -> str:
        """创建报告，返回报告 ID"""
        pass

    def get_by_id(self, report_id: str, user_id: int | None = None) -> Optional[ReportDetail]:
        """获取报告详情

        Args:
            report_id: 报告 ID
            user_id: 如果提供，只返回该用户的报告（鉴权）

        Returns:
            报告详情或 None
        """
        pass

    def list_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[ReportListItem], int]:
        """获取用户报告列表（分页）

        Returns:
            (报告列表, 总数)
        """
        pass

    def delete(self, report_id: str, user_id: int) -> bool:
        """软删除报告（鉴权）

        Returns:
            是否删除成功
        """
        pass

    def hard_delete(self, report_id: str) -> bool:
        """物理删除报告（管理员）"""
        pass

    def ensure_indexes(self) -> None:
        """创建索引"""
        self.collection.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        self.collection.create_index([("deleted_at", ASCENDING)])
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| MongoClient | TASK-002 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/repositories/test_report_repo.py
import pytest
from datetime import datetime


class TestReportRepository:
    """报告仓库测试"""

    def test_create_report(self, mongo_db):
        """测试创建报告"""
        pass

    def test_get_by_id_success(self, mongo_db):
        """测试获取报告成功"""
        pass

    def test_get_by_id_not_found(self, mongo_db):
        """测试获取不存在的报告"""
        pass

    def test_get_by_id_with_auth(self, mongo_db):
        """测试带鉴权的获取"""
        pass

    def test_get_by_id_wrong_user(self, mongo_db):
        """测试获取其他用户的报告返回 None"""
        pass

    def test_list_by_user(self, mongo_db):
        """测试用户报告列表"""
        pass

    def test_list_pagination(self, mongo_db):
        """测试分页"""
        pass

    def test_delete_success(self, mongo_db):
        """测试软删除成功"""
        pass

    def test_delete_wrong_user(self, mongo_db):
        """测试删除其他用户的报告失败"""
        pass

    def test_list_excludes_deleted(self, mongo_db):
        """测试列表不包含已删除报告"""
        pass
```

**测试用例清单**：
- [ ] 创建报告成功
- [ ] 获取报告成功
- [ ] 获取不存在报告返回 None
- [ ] 带鉴权获取成功
- [ ] 获取其他用户报告返回 None
- [ ] 用户报告列表正确
- [ ] 分页正确
- [ ] 软删除成功
- [ ] 删除其他用户报告失败
- [ ] 列表不包含已删除报告

### Step 2: 实现功能

1. 创建 MongoDB 文档模型
2. 创建 Pydantic 模型
3. 创建 Repository 类
4. 创建索引

### Step 3: 验证通过

```bash
pytest test/repositories/test_report_repo.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）

## 参考资源

### 相关文档

- [ITERATION_AUTH_PLAN.md - 4.3 MongoDB 集合结构](../ITERATION_AUTH_PLAN.md#43-mongodb-集合结构)

## 注意事项

1. **ObjectId 处理**: MongoDB 的 _id 是 ObjectId 类型，需要正确处理
2. **软删除**: 使用 deleted_at 字段，查询时过滤
3. **用户鉴权**: get_by_id 和 delete 需要验证 user_id
4. **索引**: 确保 user_id + created_at 索引
