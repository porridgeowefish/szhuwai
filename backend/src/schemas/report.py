"""
报告 Pydantic 模型
=================
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReportListItem(BaseModel):  # type: ignore[misc]
    """报告列表项

    用于列表展示，包含基本信息。
    """

    id: str = Field(..., description="报告 ID")
    plan_name: str = Field(..., description="计划名称")
    trip_date: str = Field(..., description="出行日期")
    overall_rating: str = Field(..., description="总体评分")
    created_at: datetime = Field(..., description="创建时间")


class ReportDetail(ReportListItem):
    """报告详情

    包含完整的报告内容。
    """

    user_id: int = Field(..., description="用户 ID")
    content: dict[str, Any] = Field(..., description="完整的计划内容")


class ReportCreate(BaseModel):  # type: ignore[misc]
    """创建报告请求"""

    user_id: int = Field(..., description="用户 ID")
    plan_name: str = Field(..., description="计划名称")
    trip_date: str = Field(..., description="出行日期")
    overall_rating: str = Field(..., description="总体评分")
    content: dict[str, Any] = Field(..., description="完整的计划内容")


class ReportListResponse(BaseModel):  # type: ignore[misc]
    """报告列表响应"""

    items: list[ReportListItem] = Field(default_factory=list, description="报告列表")
    pagination: dict[str, Any] = Field(default_factory=dict, description="分页信息")
