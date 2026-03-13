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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="户外活动智能规划系统 API",
    description="为 React 前端提供户外活动规划服务",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/api/generate-plan", response_model=PlanResponse)
async def generate_plan(
    user_request: str = Form(...),
    file: Optional[UploadFile] = File(None)
) -> PlanResponse:
    """
    生成户外活动计划

    接收用户请求和可选的 GPX/KML 轨迹文件，调用 Planner 生成完整的户外活动计划。

    - **user_request**: 用户请求描述（表单字段）
    - **file**: 可选的轨迹文件（.gpx 或 .kml）
    """
    temp_file_path = None
    logger.info(f"收到计划生成请求: {user_request}")

    try:
        # 处理文件上传
        if file:
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
            with open(temp_file_path, "wb") as f:
                f.write(content)

            logger.info(f"已保存临时文件: {temp_file_path}")

        # 调用规划器生成计划
        plan = router.execute_planning(
            user_request=user_request,
            gpx_path=str(temp_file_path) if temp_file_path else None
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


@app.post("/api/generate-plan/simple")
async def generate_plan_simple(
    user_request: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """
    简化版生成计划接口

    支持文件上传，使用 Form + File 方式。
    """
    temp_file_path = None

    try:
        # 处理文件上传
        if file:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ['.gpx', '.kml']:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件格式: {file_ext}，仅支持 .gpx 和 .kml"
                )

            unique_filename = f"{uuid.uuid4()}{file_ext}"
            temp_file_path = TEMP_TRACKS_DIR / unique_filename

            content = await file.read()
            with open(temp_file_path, "wb") as f:
                f.write(content)

        plan = router.execute_planning(
            user_request=user_request,
            gpx_path=str(temp_file_path) if temp_file_path else None
        )

        return plan

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)