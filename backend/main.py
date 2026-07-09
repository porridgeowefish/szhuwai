"""
FastAPI Server
==============

为 React 前端提供 RESTful API 接口。

启动命令:
    uvicorn main:app --reload --port 8000
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入模块化路由
from src.api.routes import (
    location_router,
    plan_router,
    runtime_router,
    two_bulu_router,
)
from src.services.two_bulu_browser_service import session_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ 常量配置 ============
API_VERSION = "v1"  # API 版本


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """管理本服务创建的浏览器生命周期。"""

    yield
    session_manager.shutdown()


# 创建 FastAPI 应用
app = FastAPI(
    title="户外活动智能规划系统 API",
    description="为 React 前端提供户外活动规划服务",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(plan_router, prefix=f"/api/{API_VERSION}")
app.include_router(location_router, prefix=f"/api/{API_VERSION}")
app.include_router(runtime_router, prefix=f"/api/{API_VERSION}")
app.include_router(two_bulu_router, prefix=f"/api/{API_VERSION}")


@app.get("/")
async def root() -> dict[str, str]:
    """根路径欢迎信息"""
    return {
        "message": "欢迎使用户外活动智能规划系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
