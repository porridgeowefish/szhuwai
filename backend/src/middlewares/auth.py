"""
认证中间件
==========

提供全局的认证检查中间件（可选使用）。

注意：通常推荐使用 FastAPI 的依赖注入方式（Depends）来实现认证，
因为依赖注入更灵活，可以针对每个路由单独控制。

此中间件主要用于需要全局认证检查的场景。
"""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件（可选）

    对所有需要认证的路径进行全局检查。

    注意：此中间件是可选的，大多数情况下推荐使用依赖注入方式。

    Attributes:
        exclude_paths: 不需要认证的路径列表
    """

    def __init__(self, app, exclude_paths: list[str] | None = None) -> None:
        """初始化认证中间件

        Args:
            app: FastAPI 应用实例
            exclude_paths: 不需要认证的路径列表（前缀匹配）
        """
        super().__init__(app)
        # 默认排除的路径
        self.exclude_paths = set(exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/sms/register",
            "/api/v1/auth/sms/login",
            "/api/v1/auth/password/reset",
            "/api/v1/auth/sms/send",
        ])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求

        Args:
            request: HTTP 请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            Response: HTTP 响应对象
        """
        # 检查路径是否需要认证
        path = request.url.path

        # 检查是否在排除列表中
        if self._is_excluded(path):
            return await call_next(request)

        # 检查 Authorization 头
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return Response(
                content='{"code": 401003, "message": "缺少 Authorization 头"}',
                status_code=401,
                media_type="application/json",
            )

        # 验证 Token 格式
        if not auth_header.startswith("Bearer "):
            return Response(
                content='{"code": 401002, "message": "Token 格式错误"}',
                status_code=401,
                media_type="application/json",
            )

        # 继续处理请求
        # 注意：实际的 Token 验证由后续的依赖注入完成
        # 这里只做基本的格式检查
        return await call_next(request)

    def _is_excluded(self, path: str) -> bool:
        """检查路径是否需要排除认证

        Args:
            path: 请求路径

        Returns:
            bool: 是否需要排除认证
        """
        # 精确匹配
        if path in self.exclude_paths:
            return True

        # 前缀匹配
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True

        return False
