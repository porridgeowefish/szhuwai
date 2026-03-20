"""
计划生成路由
============

POST /api/v1/plan/generate - 生成户外活动计划
"""

from typing import Optional

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel, Field

from src.schemas.output import OutdoorActivityPlan
from src.domain.orchestrator import OutdoorPlannerRouter

router = APIRouter(prefix="/plan", tags=["计划生成"])


class PlanGenerateResponse(BaseModel):
    """计划生成响应"""
    success: bool = Field(True, description="请求是否成功")
    data: Optional[OutdoorActivityPlan] = Field(None, description="生成的户外活动计划")
    message: Optional[str] = Field(None, description="附加消息")


@router.post("/generate", response_model=PlanGenerateResponse)
async def generate_plan(
    trip_date: str = Form(..., description="出行时间(YYYY-MM-DD)"),
    departure_point: str = Form(..., description="出发地点"),
    additional_info: str = Form("", description="补充信息"),
    gpx_path: str = Form(..., description="已上传的轨迹文件路径"),
    plan_title: str = Form(..., description="线路名称/计划书标题"),
    key_destinations: str = Form(..., description="核心目的地，逗号分隔")
) -> PlanGenerateResponse:
    """
    生成户外活动计划（使用已解析的轨迹）

    - **trip_date**: 出行时间（YYYY-MM-DD，必填）
    - **departure_point**: 出发地点（必填）
    - **additional_info**: 补充信息（可选）
    - **gpx_path**: 已上传的轨迹文件路径（必填）
    - **plan_title**: 线路名称/计划书标题（必填）
    - **key_destinations**: 核心目的地，逗号分隔（必填）
    """
    # 验证必填字段
    if not plan_title or not plan_title.strip():
        raise HTTPException(
            status_code=400,
            detail="plan_title（线路名称）是必填项"
        )

    if not key_destinations or not key_destinations.strip():
        raise HTTPException(
            status_code=400,
            detail="key_destinations（核心目的地）是必填项"
        )

    # 解析核心目的地列表
    destinations_list = [d.strip() for d in key_destinations.split(',') if d.strip()]
    if len(destinations_list) == 0:
        raise HTTPException(
            status_code=400,
            detail="key_destinations（核心目的地）至少需要1个有效目的地"
        )

    try:
        planner = OutdoorPlannerRouter()

        plan = planner.execute_planning(
            trip_date=trip_date,
            departure_point=departure_point,
            additional_info=additional_info,
            gpx_path=gpx_path,
            plan_title=plan_title,
            key_destinations=destinations_list
        )

        return PlanGenerateResponse(
            success=True,
            data=plan,
            message="计划生成成功"
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成计划时发生错误: {str(e)}")
