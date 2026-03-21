# TASK-019 改造 generate-plan API

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 0.5 天 |
| 前置任务 | TASK-011, TASK-014, TASK-016 |
| 后继任务 | TASK-020 |

## 任务目标

改造现有的 `/api/v1/generate-plan` API，集成用户认证、额度检查和报告保存功能。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/api/routes/plan.py` | 改造，添加认证和额度检查 |
| `src/domain/orchestrator.py` | 改造，返回 user_id 以便保存报告 |
| `main.py` | 改造，移除旧的 generate-plan 路由 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/services/quota_service.py` | 由 TASK-014 负责 |
| `src/services/report_service.py` | 由 TASK-016 负责 |
| `src/schemas/output.py` | 保持现有模型不变 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| 无 | 本任务为改造现有代码 |

## 技术规格

### 改造后的路由

```python
# src/api/routes/plan.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from src.api.deps import CurrentUser
from src.services.quota_service import QuotaService
from src.services.report_service import ReportService
from src.domain.orchestrator import OutdoorPlannerRouter

router = APIRouter(tags=["规划"])


@router.post("/generate-plan")
async def generate_plan(
    trip_date: str = Form(...),
    departure_point: str = Form(...),
    additional_info: str = Form(""),
    file: UploadFile = File(...),
    plan_title: str = Form(...),
    key_destinations: str = Form(...),
    user: CurrentUser = Depends(),
    quota_service: QuotaService = Depends(),
    report_service: ReportService = Depends()
):
    """生成户外活动计划（需要登录）

    新增功能：
    - 需要登录认证
    - 检查额度限制
    - 自动保存报告
    """
    # 1. 检查额度
    quota_check = quota_service.check_quota(user.id)
    if not quota_check.has_quota:
        raise HTTPException(
            status_code=403,
            detail={
                "code": 403003,
                "message": f"今日额度已用完，剩余 {quota_check.remaining} 次"
            }
        )

    # 2. 调用原有规划逻辑
    planner = OutdoorPlannerRouter()
    plan = planner.execute_planning(
        trip_date=trip_date,
        departure_point=departure_point,
        additional_info=additional_info,
        gpx_path=save_temp_file(file),
        plan_title=plan_title,
        key_destinations=parse_destinations(key_destinations)
    )

    # 3. 消耗额度
    quota_service.consume_quota(user.id)

    # 4. 保存报告
    plan_dict = plan.model_dump()
    plan_dict["user_id"] = user.id
    report_id = report_service.create(user.id, plan_dict)

    # 5. 返回结果（包含报告 ID）
    return {
        "success": True,
        "data": plan,
        "message": "计划生成成功",
        "report_id": report_id
    }
```

### 错误处理

```python
# 新增错误码
401001: "未登录"  # 由中间件处理
403003: "今日额度已用完"
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| CurrentUser | TASK-011 | 待完成 |
| QuotaService | TASK-014 | 待完成 |
| ReportService | TASK-016 | 待完成 |
| OutdoorPlannerRouter | 已存在 | 可用 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/api/routes/test_plan_integration.py
class TestGeneratePlanIntegration:
    """generate-plan 集成测试"""

    def test_generate_plan_success(self, client, auth_header, sample_file):
        """测试生成计划成功"""
        pass

    def test_generate_plan_unauthorized(self, client, sample_file):
        """测试未登录"""
        pass

    def test_generate_plan_quota_exhausted(self, client, auth_header, sample_file):
        """测试额度耗尽"""
        pass

    def test_generate_plan_quota_consumed(self, client, auth_header, sample_file):
        """测试额度被消耗"""
        pass

    def test_generate_plan_report_saved(self, client, auth_header, sample_file):
        """测试报告被保存"""
        pass

    def test_generate_plan_admin_unlimited(self, client, admin_auth_header, sample_file):
        """测试管理员无额度限制"""
        pass
```

**测试用例清单**：
- [ ] 生成计划成功
- [ ] 未登录返回 401
- [ ] 额度耗尽返回 403
- [ ] 额度被消耗
- [ ] 报告被保存
- [ ] 管理员无额度限制

### Step 2: 实现功能

1. 修改 `src/api/routes/plan.py`
2. 添加认证依赖
3. 添加额度检查
4. 添加报告保存
5. 更新 `main.py` 移除旧的 generate-plan

### Step 3: 验证通过

```bash
pytest test/api/routes/test_plan_integration.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 原有功能不受影响
- [ ] 新增功能正常工作

## 参考资源

### 现有代码参考

| 文件 | 参考内容 |
|------|----------|
| `main.py:102-219` | 原有 generate-plan 实现 |

### 相关文档

- [ITERATION_AUTH_PLAN.md - 3.4.16 POST /generate-plan](../ITERATION_AUTH_PLAN.md#3416-post-generate-plan改造)

## 注意事项

1. **向后兼容**: 保持原有的请求参数和响应格式
2. **原子性**: 额度消耗和报告保存应该在同一事务中
3. **错误处理**: 规划失败时不消耗额度
4. **临时文件**: 保持原有的临时文件处理逻辑
