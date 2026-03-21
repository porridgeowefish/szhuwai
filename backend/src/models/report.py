"""
报告 MongoDB 文档模型
====================
"""

from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, Field


class ReportDocument(BaseModel):  # type: ignore[misc]
    """报告 MongoDB 文档模型

    用于映射 MongoDB 中的 reports 集合。
    """

    id: Optional[ObjectId] = Field(None, alias="_id", description="MongoDB ObjectId")
    user_id: int = Field(..., description="用户 ID")
    plan_name: str = Field(..., description="计划名称")
    trip_date: str = Field(..., description="出行日期")
    overall_rating: str = Field(..., description="总体评分")
    content: dict[str, Any] = Field(..., description="完整的计划内容")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    deleted_at: Optional[datetime] = Field(None, description="软删除时间")

    class Config:
        """Pydantic 配置"""

        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
