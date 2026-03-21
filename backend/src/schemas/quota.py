"""
额度 Pydantic 模型
=================

定义额度相关的数据契约模型。
"""

from datetime import datetime

from pydantic import BaseModel, Field


class QuotaInfo(BaseModel):
    """额度信息

    包含用户额度的详细信息。
    """

    used: int = Field(..., description="已使用次数", ge=0)
    total: int = Field(..., description="总额度", ge=-1)
    remaining: int = Field(..., description="剩余额度", ge=-1)
    reset_at: datetime = Field(..., description="重置时间（明日0点）")

    @property
    def is_unlimited(self) -> bool:
        """是否无限制（管理员）

        当 remaining 为 -1 时表示无限制额度。
        """
        return self.remaining == -1


class QuotaResponse(BaseModel):
    """额度查询响应

    API 返回的额度信息标准格式。
    """

    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: QuotaInfo = Field(..., description="额度信息")
