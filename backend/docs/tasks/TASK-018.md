# TASK-018 用户管理 API 路由

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 0.5 天 |
| 前置任务 | TASK-005, TASK-011 |
| 后继任务 | TASK-019 |

## 任务目标

实现用户管理相关的 API 路由，仅供管理员使用。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/api/routes/users.py` | 新建，用户管理路由 |
| `src/api/routes/__init__.py` | 扩展，导出新路由 |
| `main.py` | 扩展，注册新路由 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/repositories/user_repo.py` | 由 TASK-005 负责 |
| `src/services/auth_service.py` | 由 TASK-009 负责 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/api/routes/users.py` | 用户管理 API 路由 |
| `test/api/routes/test_users.py` | API 测试 |

## 技术规格

### 用户管理路由

```python
# src/api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.deps import AdminUser
from src.repositories.user_repo import UserRepository

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("")
async def list_users(
    admin: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_repo: UserRepository = Depends()
):
    """获取用户列表（管理员）"""
    users, total = user_repo.list_users(page, page_size)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "list": [
                {
                    "id": u.id,
                    "username": u.username,
                    "phone": u.phone[:3] + "****" + u.phone[-4:] if u.phone else None,
                    "role": u.role,
                    "status": u.status,
                    "createdAt": u.created_at.isoformat(),
                    "lastLoginAt": u.last_login_at.isoformat() if u.last_login_at else None
                }
                for u in users
            ],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size
            }
        }
    }


@router.patch("/{user_id}/status")
async def update_user_status(
    user_id: int,
    request: UpdateStatusRequest,
    admin: AdminUser,
    user_repo: UserRepository = Depends()
):
    """更新用户状态（管理员）"""
    if request.status not in ["active", "disabled"]:
        raise HTTPException(
            status_code=400,
            detail={"code": 400001, "message": "状态值无效"}
        )

    # 不能禁用自己
    if user_id == admin.id:
        raise HTTPException(
            status_code=400,
            detail={"code": 400001, "message": "不能禁用自己"}
        )

    success = user_repo.update_status(user_id, request.status)
    if not success:
        raise HTTPException(
            status_code=404,
            detail={"code": 404001, "message": "用户不存在"}
        )

    return {
        "code": 200,
        "message": "状态更新成功",
        "data": {"id": user_id, "status": request.status}
    }


class UpdateStatusRequest(BaseModel):
    status: str
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| UserRepository | TASK-005 | 待完成 |
| AdminUser | TASK-011 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/api/routes/test_users.py
class TestUsersRoutes:
    """用户管理 API 测试"""

    def test_list_users_as_admin(self, client, admin_auth_header):
        """测试管理员获取用户列表"""
        pass

    def test_list_users_as_normal_user(self, client, auth_header):
        """测试普通用户获取用户列表（应失败）"""
        pass

    def test_update_status_success(self, client, admin_auth_header):
        """测试更新用户状态"""
        pass

    def test_update_status_cannot_disable_self(self, client, admin_auth_header):
        """测试不能禁用自己"""
        pass

    def test_update_status_invalid_status(self, client, admin_auth_header):
        """测试无效状态值"""
        pass

    def test_update_status_user_not_found(self, client, admin_auth_header):
        """测试用户不存在"""
        pass
```

**测试用例清单**：
- [ ] GET /users 管理员成功
- [ ] GET /users 普通用户失败
- [ ] PATCH /users/{id}/status 成功
- [ ] 不能禁用自己
- [ ] 无效状态值
- [ ] 用户不存在

### Step 2: 实现功能

1. 创建 `src/api/routes/users.py`
2. 更新 `main.py`

### Step 3: 验证通过

```bash
pytest test/api/routes/test_users.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] API 文档正确生成（/docs）

## 参考资源

### 相关文档

- [ITERATION_AUTH_PLAN.md - 3.4.10 GET /users](../ITERATION_AUTH_PLAN.md#3410-get-users)
- [ITERATION_AUTH_PLAN.md - 3.4.11 PATCH /users/{id}/status](../ITERATION_AUTH_PLAN.md#3411-patch-usersidstatus)

## 注意事项

1. **管理员权限**: 使用 AdminUser 依赖确保只有管理员可访问
2. **手机号脱敏**: 返回列表时手机号需要脱敏
3. **自我保护**: 不能禁用自己
