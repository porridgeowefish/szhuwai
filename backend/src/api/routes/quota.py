"""
额度路由
========
"""

from typing import Any

from fastapi import APIRouter, Depends

from src.api.deps import CurrentUser
from src.infrastructure.mysql_client import get_db
from src.repositories.quota_repo import QuotaRepository
from src.repositories.user_repo import UserRepository
from src.services.quota_service import QuotaService

router = APIRouter(prefix="/quota", tags=["额度"])


# ============ 依赖注入 ============
def get_quota_service() -> QuotaService:
    """获取额度服务实例"""
    db = next(get_db())
    quota_repo = QuotaRepository(db)
    user_repo = UserRepository(db)
    return QuotaService(quota_repo=quota_repo, user_repo=user_repo)


# ============ 路由 ============


@router.get("")
async def get_quota(
    user: CurrentUser,
    quota_service: QuotaService = Depends(get_quota_service),
) -> dict[str, Any]:
    """
    获取今日剩余额度

    返回当前用户的额度使用情况，包括已使用次数、总额度和剩余额度。
    管理员用户返回无限制额度（remaining=-1）。

    - **used**: 今日已使用次数
    - **total**: 总额度（管理员为 -1）
    - **remaining**: 剩余额度（管理员为 -1）
    - **resetAt**: 下次重置时间（明日 0 点）
    """
    quota_info = quota_service.get_quota_info(user.id)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "used": quota_info.used,
            "total": quota_info.total,
            "remaining": quota_info.remaining,
            "resetAt": quota_info.reset_at.isoformat(),
        },
    }
