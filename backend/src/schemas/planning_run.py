"""规划运行过程的轻量监控契约。"""

from typing import Literal

from pydantic import BaseModel, Field


StageStatus = Literal["success", "degraded", "failed", "skipped"]


class PlanningStageLog(BaseModel):
    """一次规划中的单个阶段记录。"""

    stage: str = Field(..., description="阶段标识")
    title: str = Field(..., description="面向用户的阶段名称")
    status: StageStatus = Field(..., description="阶段状态")
    duration_ms: int = Field(..., ge=0, description="阶段耗时，毫秒")
    message: str = Field(default="", description="阶段结果或降级原因")


class PlanningRunReport(BaseModel):
    """一次规划请求的运行回执。"""

    run_id: str = Field(..., description="本次规划运行 ID")
    strategy: Literal["fast", "ai"] = Field(..., description="生成策略")
    total_duration_ms: int = Field(..., ge=0, description="总耗时，毫秒")
    stages: list[PlanningStageLog] = Field(default_factory=list, description="阶段时间线")
    warnings: list[str] = Field(default_factory=list, description="降级或风险提示")
