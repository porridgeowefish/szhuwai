"""
FastAPI Server
==============

为 React 前端提供 RESTful API 接口。

启动命令:
    uvicorn main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入模块化路由
from src.api.routes import (
    track_router,
    weather_router,
    transport_router,
    search_router,
    plan_router,
    auth_router,
    sms_router,
    quota_router,
    reports_router,
    users_router,
)

# 导入配置和基础设施
from src.api.config import api_config
from src.infrastructure.mysql_client import init_mysql_client
from src.infrastructure.jwt_handler import init_jwt_handler
from src.infrastructure.aliyun_sms_client import init_aliyun_sms_client
from src.infrastructure.mongo_client import init_mongo_client

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ 常量配置 ============
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


# ============ 应用启动事件 ============
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化基础设施"""
    logger.info("初始化基础设施...")

    # 初始化 MySQL 客户端
    try:
        init_mysql_client(api_config)
        logger.info("MySQL 客户端初始化成功")
    except Exception as e:
        logger.warning(f"MySQL 客户端初始化失败: {e}")

    # 初始化 JWT 处理器
    try:
        init_jwt_handler(api_config)
        logger.info("JWT 处理器初始化成功")
    except Exception as e:
        logger.warning(f"JWT 处理器初始化失败: {e}")

    # 初始化短信客户端
    try:
        init_aliyun_sms_client(api_config)
        logger.info("短信客户端初始化成功")
    except Exception as e:
        logger.warning(f"短信客户端初始化失败: {e}")

    # 初始化 MongoDB 客户端
    try:
        init_mongo_client(api_config)
        logger.info("MongoDB 客户端初始化成功")
    except Exception as e:
        logger.warning(f"MongoDB 客户端初始化失败: {e}")

# ============ 注册模块化路由 ============
app.include_router(track_router, prefix=f"/api/{API_VERSION}")
app.include_router(weather_router, prefix=f"/api/{API_VERSION}")
app.include_router(transport_router, prefix=f"/api/{API_VERSION}")
app.include_router(search_router, prefix=f"/api/{API_VERSION}")
app.include_router(plan_router, prefix=f"/api/{API_VERSION}")
app.include_router(sms_router, prefix=f"/api/{API_VERSION}")
app.include_router(auth_router, prefix=f"/api/{API_VERSION}")
app.include_router(quota_router, prefix=f"/api/{API_VERSION}")
app.include_router(reports_router, prefix=f"/api/{API_VERSION}")
app.include_router(users_router, prefix=f"/api/{API_VERSION}")


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)