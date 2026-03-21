"""
计划生成路由
============

POST /api/v1/plan/generate - 生成户外活动计划（需要认证）
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.schemas.output import OutdoorActivityPlan
from src.domain.orchestrator import OutdoorPlannerRouter
from src.api.deps import CurrentUser, get_user_repo
from src.infrastructure.mysql_client import get_db
from src.infrastructure.mongo_client import get_mongo_client
from src.repositories.user_repo import UserRepository
from src.repositories.quota_repo import QuotaRepository
from src.repositories.report_repo import ReportRepository
from src.services.quota_service import QuotaService
from src.services.report_service import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plan", tags=["计划生成"])

# 常量配置
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
TEMP_TRACKS_DIR = Path("temp_tracks")
TEMP_TRACKS_DIR.mkdir(exist_ok=True)


class PlanGenerateResponse(BaseModel):
    """计划生成响应"""
    success: bool = Field(True, description="请求是否成功")
    data: OutdoorActivityPlan = Field(..., description="生成的户外活动计划")
    message: str = Field(..., description="附加消息")
    report_id: str = Field(..., description="报告 ID")


# ============ 依赖注入工厂函数 ============

def get_quota_service(
    db: Annotated[Session, Depends(get_db)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)]
) -> QuotaService:
    """获取额度服务实例"""
    quota_repo = QuotaRepository(db)
    return QuotaService(quota_repo=quota_repo, user_repo=user_repo)


def get_report_service() -> ReportService:
    """获取报告服务实例"""
    mongo_client = get_mongo_client()
    report_repo = ReportRepository(mongo_client.db)
    return ReportService(report_repo=report_repo)


@router.post("/generate", response_model=PlanGenerateResponse)
async def generate_plan(
    user: CurrentUser,
    quota_service: QuotaService = Depends(get_quota_service),
    report_service: ReportService = Depends(get_report_service),
    trip_date: str = Form(..., description="出行时间(YYYY-MM-DD)"),
    departure_point: str = Form(..., description="出发地点"),
    additional_info: str = Form("", description="补充信息"),
    file: UploadFile = File(..., description="GPX/KML 轨迹文件"),
    plan_title: str = Form(..., description="线路名称/计划书标题"),
    key_destinations: str = Form(..., description="核心目的地，逗号分隔")
) -> PlanGenerateResponse:
    """
    生成户外活动计划（需要登录）

    新增功能：
    - 需要登录认证
    - 检查额度限制
    - 自动保存报告

    - **trip_date**: 出行时间（YYYY-MM-DD，必填）
    - **departure_point**: 出发地点（必填）
    - **additional_info**: 补充信息（可选）
    - **file**: GPX/KML 轨迹文件（必填）
    - **plan_title**: 线路名称/计划书标题（必填）
    - **key_destinations**: 核心目的地，逗号分隔（必填）
    """
    temp_file_path = None

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

        # 2. 保存临时文件
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""
        if file_ext not in ['.gpx', '.kml']:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_ext}，仅支持 .gpx 和 .kml"
            )

        unique_filename = f"{uuid.uuid4()}{file_ext}"
        temp_file_path = TEMP_TRACKS_DIR / unique_filename

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）"
            )

        with open(temp_file_path, "wb") as f:
            f.write(content)

        logger.info(f"已保存临时文件: {temp_file_path}")

        # 3. 调用规划逻辑
        planner = OutdoorPlannerRouter()
        plan = planner.execute_planning(
            trip_date=trip_date,
            departure_point=departure_point,
            additional_info=additional_info,
            gpx_path=str(temp_file_path),
            plan_title=plan_title,
            key_destinations=destinations_list
        )

        # 4. 消耗额度
        quota_service.consume_quota(user.id)

        # 5. 保存报告
        plan_dict = plan.model_dump()
        report_id = report_service.create(user.id, plan_dict)

        logger.info(f"计划生成成功: {plan.plan_id}, 报告 ID: {report_id}")

        return PlanGenerateResponse(
            success=True,
            data=plan,
            message="计划生成成功",
            report_id=report_id
        )

    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"生成计划时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"生成计划时发生错误: {str(e)}")
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"已清理临时文件: {temp_file_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
