"""
FastAPI Server
==============

为 React 前端提供 RESTful API 接口。

启动命令:
    uvicorn main:app --reload --port 8000
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.domain.orchestrator import OutdoorPlannerRouter
from src.schemas.output import OutdoorActivityPlan

# 导入模块化路由
from src.api.routes import (
    track_router,
    weather_router,
    transport_router,
    search_router,
    plan_router
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ 常量配置 ============
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB - 文件上传大小限制
API_VERSION = "v1"  # API 版本

# 创建 FastAPI 应用
app = FastAPI(
    title="户外活动智能规划系统 API",
    description="为 React 前端提供户外活动规划服务",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 注册模块化路由 ============
app.include_router(track_router, prefix=f"/api/{API_VERSION}")
app.include_router(weather_router, prefix=f"/api/{API_VERSION}")
app.include_router(transport_router, prefix=f"/api/{API_VERSION}")
app.include_router(search_router, prefix=f"/api/{API_VERSION}")
app.include_router(plan_router, prefix=f"/api/{API_VERSION}")


# 响应体模型
class PlanResponse(BaseModel):
    """API 响应包装"""
    success: bool = Field(True, description="请求是否成功")
    data: OutdoorActivityPlan = Field(..., description="生成的户外活动计划")
    message: Optional[str] = Field(None, description="附加消息")


# 全局路由器实例
router = OutdoorPlannerRouter()

# 临时文件目录
TEMP_TRACKS_DIR = Path("temp_tracks")
TEMP_TRACKS_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """根路径欢迎信息"""
    return {
        "message": "欢迎使用户外活动智能规划系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post(f"/api/{API_VERSION}/generate-plan", response_model=PlanResponse)
async def generate_plan(
    trip_date: str = Form(..., description="出行时间(YYYY-MM-DD)"),
    departure_point: str = Form(..., description="出发地点(供高德解析使用，需尽量详细)"),
    additional_info: str = Form("", description="补充信息"),
    file: UploadFile = File(..., description="GPX/KML 轨迹文件（必填）"),
    plan_title: str = Form(..., description="线路名称/计划书标题（必填）"),
    key_destinations: str = Form(..., description="核心目的地，逗号分隔（至少1个，必填）")
) -> PlanResponse:
    """
    生成户外活动计划

    接收出行时间、出发地点、补充信息、轨迹文件和核心目的地，调用 Planner 生成完整的户外活动计划。

    - **trip_date**: 出行时间（YYYY-MM-DD，必填）
    - **departure_point**: 出发地点（供高德解析使用，需尽量详细，必填）
    - **additional_info**: 补充信息（可选）
    - **file**: GPX/KML 轨迹文件（必填）
    - **plan_title**: 线路名称/计划书标题（必填）
    - **key_destinations**: 核心目的地，逗号分隔（至少1个，必填）
    """
    temp_file_path = None
    logger.info(f"收到计划生成请求: trip_date={trip_date}, departure_point={departure_point}")

    # 验证必填字段
    if not trip_date or not departure_point or not file:
        raise HTTPException(
            status_code=400,
            detail="trip_date、departure_point 和 file 都是必填项"
        )

    # 验证新必填字段
    if not plan_title or not plan_title.strip():
        raise HTTPException(
            status_code=400,
            detail="plan_title（线路名称）是必填项"
        )

    if not key_destinations or not key_destinations.strip():
        raise HTTPException(
            status_code=400,
            detail="key_destinations（核心目的地）是必填项，至少填写1个"
        )

    # 解析核心目的地列表
    destinations_list = [d.strip() for d in key_destinations.split(',') if d.strip()]
    if len(destinations_list) == 0:
        raise HTTPException(
            status_code=400,
            detail="key_destinations（核心目的地）至少需要1个有效目的地"
        )

    try:
        # 验证文件后缀名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.gpx', '.kml']:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_ext}，仅支持 .gpx 和 .kml"
            )

        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        temp_file_path = TEMP_TRACKS_DIR / unique_filename

        # 保存上传的文件
        content = await file.read()

        # 文件大小检查
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）"
            )

        with open(temp_file_path, "wb") as f:
            f.write(content)

        logger.info(f"已保存临时文件: {temp_file_path}")

        # 调用规划器生成计划
        plan = router.execute_planning(
            trip_date=trip_date,
            departure_point=departure_point,
            additional_info=additional_info,
            gpx_path=str(temp_file_path),
            plan_title=plan_title,
            key_destinations=destinations_list
        )
        logger.info(f"计划生成成功: {plan.plan_id}")

        return PlanResponse(
            success=True,
            data=plan,
            message="计划生成成功"
        )

    except HTTPException:
        # 直接重新抛出 HTTP 异常
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)