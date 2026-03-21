"""
报告路由
========
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import CurrentUser
from src.infrastructure.mongo_client import get_mongo_client
from src.repositories.report_repo import ReportRepository
from src.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["报告"])


# ============ 依赖注入 ============
def get_report_service() -> ReportService:
    """获取报告服务实例"""
    mongo_client = get_mongo_client()
    report_repo = ReportRepository(mongo_client.db)
    return ReportService(report_repo=report_repo)


# ============ 路由 ============


@router.get("")
async def list_reports(
    user: CurrentUser,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    report_service: ReportService = Depends(get_report_service),
) -> dict[str, Any]:
    """
    获取我的报告列表

    返回当前登录用户的报告列表，按创建时间倒序排列。

    - **page**: 页码，从 1 开始
    - **page_size**: 每页数量，范围 1-100

    返回包含报告列表和分页信息。
    """
    reports, pagination = report_service.list_by_user(user.id, page, page_size)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "list": [r.model_dump() for r in reports],
            "pagination": {
                "page": pagination["page"],
                "pageSize": pagination["page_size"],
                "total": pagination["total"],
                "totalPages": pagination["total_pages"],
            },
        },
    }


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user: CurrentUser,
    report_service: ReportService = Depends(get_report_service),
) -> dict[str, Any]:
    """
    获取报告详情

    根据报告 ID 获取报告的完整内容。
    只能查看自己的报告。

    - **report_id**: 报告 ID（MongoDB ObjectId）

    返回完整的报告内容，包括计划数据。
    """
    report = report_service.get_by_id(report_id, user.id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": 404001, "message": "报告不存在或无权访问"},
        )

    return {
        "code": 200,
        "message": "success",
        "data": report.model_dump(),
    }


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    user: CurrentUser,
    report_service: ReportService = Depends(get_report_service),
) -> dict[str, Any]:
    """
    删除报告

    软删除指定的报告。
    只能删除自己的报告。

    - **report_id**: 报告 ID（MongoDB ObjectId）

    成功删除后返回确认信息。
    """
    success = report_service.delete(report_id, user.id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail={"code": 404001, "message": "报告不存在或无权删除"},
        )

    return {
        "code": 200,
        "message": "删除成功",
        "data": None,
    }
