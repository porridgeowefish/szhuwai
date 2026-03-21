# TASK-017 额度与报告 API 路由

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 0.5 天 |
| 前置任务 | TASK-014, TASK-016 |
| 后继任务 | TASK-019 |

## 任务目标

实现额度和报告相关的 API 路由，提供 RESTful 接口供前端调用。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/api/routes/quota.py` | 新建，额度路由 |
| `src/api/routes/reports.py` | 新建，报告路由 |
| `src/api/routes/__init__.py` | 扩展，导出新路由 |
| `main.py` | 扩展，注册新路由 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/services/quota_service.py` | 由 TASK-014 负责 |
| `src/services/report_service.py` | 由 TASK-016 负责 |
| 现有 `src/api/routes/plan.py` | 保持现有逻辑 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/api/routes/quota.py` | 额度 API 路由 |
| `src/api/routes/reports.py` | 报告 API 路由 |
| `test/api/routes/test_quota.py` | API 测试 |
| `test/api/routes/test_reports.py` | API 测试 |

## 技术规格

### 额度路由

```python
# src/api/routes/quota.py
from fastapi import APIRouter, Depends
from src.api.deps import CurrentUser
from src.services.quota_service import QuotaService

router = APIRouter(prefix="/quota", tags=["额度"])


@router.get("")
async def get_quota(
    user: CurrentUser,
    quota_service: QuotaService = Depends()
):
    """获取今日剩余额度"""
    quota_info = quota_service.get_quota_info(user.id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "used": quota_info.used,
            "total": quota_info.total,
            "remaining": quota_info.remaining,
            "resetAt": quota_info.reset_at.isoformat()
        }
    }
```

### 报告路由

```python
# src/api/routes/reports.py
from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.deps import CurrentUser
from src.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["报告"])


@router.get("")
async def list_reports(
    user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    report_service: ReportService = Depends()
):
    """获取我的报告列表"""
    reports, total = report_service.list_by_user(user.id, page, page_size)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "list": [r.model_dump() for r in reports],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size
            }
        }
    }


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user: CurrentUser,
    report_service: ReportService = Depends()
):
    """获取报告详情"""
    report = report_service.get_by_id(report_id, user.id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail={"code": 404001, "message": "报告不存在"}
        )
    return {
        "code": 200,
        "message": "success",
        "data": report.model_dump()
    }


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    user: CurrentUser,
    report_service: ReportService = Depends()
):
    """删除报告"""
    success = report_service.delete(report_id, user.id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail={"code": 404001, "message": "报告不存在或无权删除"}
        )
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }
```

### main.py 集成

```python
# main.py 新增
from src.api.routes import (
    # ... 现有路由 ...
    quota_router,
    reports_router
)

# 注册路由
app.include_router(quota_router, prefix=f"/api/{API_VERSION}")
app.include_router(reports_router, prefix=f"/api/{API_VERSION}")
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| QuotaService | TASK-014 | 待完成 |
| ReportService | TASK-016 | 待完成 |
| CurrentUser | TASK-011 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/api/routes/test_quota.py
class TestQuotaRoutes:
    """额度 API 测试"""

    def test_get_quota_normal_user(self, client, auth_header):
        """测试普通用户获取额度"""
        pass

    def test_get_quota_admin_user(self, client, admin_auth_header):
        """测试管理员获取额度（无限制）"""
        pass

    def test_get_quota_unauthorized(self, client):
        """测试未授权访问"""
        pass


# test/api/routes/test_reports.py
class TestReportRoutes:
    """报告 API 测试"""

    def test_list_reports(self, client, auth_header):
        """测试获取报告列表"""
        pass

    def test_get_report_success(self, client, auth_header):
        """测试获取报告详情"""
        pass

    def test_get_report_not_found(self, client, auth_header):
        """测试获取不存在的报告"""
        pass

    def test_get_report_not_owner(self, client, auth_header):
        """测试获取他人报告"""
        pass

    def test_delete_report_success(self, client, auth_header):
        """测试删除报告"""
        pass

    def test_delete_report_not_owner(self, client, auth_header):
        """测试删除他人报告"""
        pass
```

**测试用例清单**：
- [ ] GET /quota 普通用户
- [ ] GET /quota 管理员（无限制）
- [ ] GET /quota 未授权
- [ ] GET /reports 列表
- [ ] GET /reports/{id} 成功
- [ ] GET /reports/{id} 不存在
- [ ] GET /reports/{id} 他人报告
- [ ] DELETE /reports/{id} 成功
- [ ] DELETE /reports/{id} 他人报告

### Step 2: 实现功能

1. 创建 `src/api/routes/quota.py`
2. 创建 `src/api/routes/reports.py`
3. 更新 `main.py`

### Step 3: 验证通过

```bash
pytest test/api/routes/test_quota.py test/api/routes/test_reports.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] API 文档正确生成（/docs）

## 参考资源

### 相关文档

- [ITERATION_AUTH_PLAN.md - 3.3 接口列表](../ITERATION_AUTH_PLAN.md#33-接口列表)

## 注意事项

1. **鉴权**: 所有接口需要 JWT 认证
2. **权限隔离**: 用户只能操作自己的报告
3. **错误码**: 使用规划文档中定义的错误码
