"""
用户管理路由
===========
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.deps import AdminUser
from src.infrastructure.mysql_client import get_db
from src.repositories.user_repo import UserRepository

router = APIRouter(prefix="/users", tags=["用户管理"])


# ============ 请求模型 ============
class UpdateStatusRequest(BaseModel):
    """更新用户状态请求"""

    status: str = Field(..., description="用户状态：active 或 disabled")


# ============ 依赖注入 ============
def get_user_repo() -> UserRepository:
    """获取用户仓库实例"""
    db = next(get_db())
    return UserRepository(db)


# ============ 路由 ============


@router.get("")
async def list_users(
    admin: AdminUser,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_repo: UserRepository = Depends(get_user_repo),
) -> dict[str, Any]:
    """
    获取用户列表（管理员）

    返回所有用户的列表，支持分页。
    仅管理员可访问。

    - **page**: 页码，从 1 开始
    - **page_size**: 每页数量，范围 1-100

    返回包含用户列表和分页信息。
    手机号已脱敏处理。
    """
    users, total = user_repo.list_users(page, page_size)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "list": [
                {
                    "id": u.id,
                    "username": u.username,
                    "phone": (
                        u.phone[:3] + "****" + u.phone[-4:]
                        if u.phone
                        else None
                    ),
                    "role": u.role,
                    "status": u.status,
                    "createdAt": u.created_at.isoformat(),
                    "lastLoginAt": (
                        u.last_login_at.isoformat() if u.last_login_at else None
                    ),
                }
                for u in users
            ],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size,
            },
        },
    }


@router.patch("/{user_id}/status")
async def update_user_status(
    user_id: int,
    request: UpdateStatusRequest,
    admin: AdminUser,
    user_repo: UserRepository = Depends(get_user_repo),
) -> dict[str, Any]:
    """
    更新用户状态（管理员）

    启用或禁用指定用户。
    仅管理员可访问。

    - **user_id**: 用户 ID
    - **status**: 用户状态（active 或 disabled）

    注意：不能禁用自己。
    """
    # 验证状态值
    if request.status not in ["active", "disabled"]:
        raise HTTPException(
            status_code=400,
            detail={"code": 400001, "message": "状态值无效"},
        )

    # 不能禁用自己
    if user_id == admin.id:
        raise HTTPException(
            status_code=400,
            detail={"code": 400001, "message": "不能禁用自己"},
        )

    # 更新状态
    success = user_repo.update_status(user_id, request.status)
    if not success:
        raise HTTPException(
            status_code=404,
            detail={"code": 404001, "message": "用户不存在"},
        )

    return {
        "code": 200,
        "message": "状态更新成功",
        "data": {"id": user_id, "status": request.status},
    }
