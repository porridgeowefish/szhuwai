"""
API Routes
==========

模块化的 API 路由定义。
"""

from .track import router as track_router
from .weather import router as weather_router
from .transport import router as transport_router
from .search import router as search_router
from .plan import router as plan_router

__all__ = [
    "track_router",
    "weather_router",
    "transport_router",
    "search_router",
    "plan_router"
]
