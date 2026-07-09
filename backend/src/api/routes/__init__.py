"""
API Routes
==========

模块化的 API 路由定义。
"""

from .plan import router as plan_router
from .location import router as location_router
from .runtime import router as runtime_router
from .two_bulu import router as two_bulu_router

__all__ = [
    "location_router",
    "plan_router",
    "runtime_router",
    "two_bulu_router",
]
