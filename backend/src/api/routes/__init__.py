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
from .auth import router as auth_router
from .sms import router as sms_router
from .quota import router as quota_router
from .reports import router as reports_router
from .users import router as users_router

__all__ = [
    "track_router",
    "weather_router",
    "transport_router",
    "search_router",
    "plan_router",
    "auth_router",
    "sms_router",
    "quota_router",
    "reports_router",
    "users_router",
]
