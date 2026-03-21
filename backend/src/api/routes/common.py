"""
认证路由通用模块
================

提供统一的 API 响应模型、错误码定义和认证依赖。
"""

from typing import Any, Generic, TypeVar

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from src.schemas.user import UserResponse

# ============ 错误码定义 ============
class ErrorCodes:
    """错误码常量"""

    # 通用错误 1xxxx
    INVALID_PARAMS = (400001, "参数错误")
    UNAUTHORIZED = (401001, "未授权，请先登录")
    TOKEN_INVALID = (401002, "Token 无效或已过期")
    TOKEN_MISSING = (401003, "缺少 Authorization 头")
    FORBIDDEN = (403001, "无权限访问")
    NOT_FOUND = (404001, "资源不存在")
    RATE_LIMITED = (429001, "请求过于频繁，请稍后再试")
    INTERNAL_ERROR = (500001, "服务器内部错误")

    # 认证错误 10xxxx
    USER_NOT_FOUND = (100001, "用户不存在")
    USER_EXISTS = (100002, "用户名已存在")
    PHONE_EXISTS = (100003, "手机号已被注册")
    PHONE_NOT_BOUND = (100004, "手机号未绑定")
    INVALID_PASSWORD = (100005, "密码错误")
    INVALID_CODE = (100006, "验证码错误")
    ACCOUNT_DISABLED = (100007, "账号已被禁用")
    PHONE_REGISTERED = (100008, "手机号已注册")
    PHONE_NOT_REGISTERED = (100009, "手机号未注册")

    @classmethod
    def get_http_status(cls, error_code: int) -> int:
        """根据错误码获取 HTTP 状态码"""
        if 400000 <= error_code < 500000:
            prefix = error_code // 1000
            return {
                400: status.HTTP_400_BAD_REQUEST,
                401: status.HTTP_401_UNAUTHORIZED,
                403: status.HTTP_403_FORBIDDEN,
                404: status.HTTP_404_NOT_FOUND,
                429: status.HTTP_429_TOO_MANY_REQUESTS,
            }.get(prefix, status.HTTP_400_BAD_REQUEST)
        return status.HTTP_500_INTERNAL_SERVER_ERROR


# ============ 响应模型 ============
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""

    code: int = Field(200, description="业务状态码")
    message: str = Field("success", description="响应消息")
    data: T | None = Field(None, description="响应数据")


class LoginData(BaseModel):
    """登录响应数据"""

    accessToken: str = Field(..., description="访问令牌")
    tokenType: str = Field("Bearer", description="令牌类型")
    expiresIn: int = Field(..., description="过期时间（秒）")
    user: UserResponse = Field(..., description="用户信息")


class UserWithToken(BaseModel):
    """用户信息（带 token）"""

    user: UserResponse = Field(..., description="用户信息")
    accessToken: str = Field(..., description="访问令牌")
    tokenType: str = Field("Bearer", description="令牌类型")
    expiresIn: int = Field(..., description="过期时间（秒）")


# ============ 认证依赖 ============
security = HTTPBearer(auto_error=False)


async def get_optional_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any] | None:
    """可选认证依赖

    尝试从请求头中解析 Token，但不强制要求。

    Returns:
        Token 载荷字典，未提供或无效时返回 None
    """
    from src.infrastructure.mysql_client import get_db

    # 获取依赖
    from src.repositories.user_repo import UserRepository
    from src.infrastructure.jwt_handler import get_jwt_handler

    if credentials is None:
        return None

    try:
        db = next(get_db())
        jwt_handler = get_jwt_handler()

        # 验证 Token
        payload = jwt_handler.verify_token(credentials.credentials)

        # 获取用户信息
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(payload.user_id)

        if user and user.status == "active":
            return {
                "user_id": payload.user_id,
                "username": payload.username,
                "role": payload.role,
            }

        return None
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """获取当前认证用户

    强制要求认证，未认证则抛出 401 异常。

    Returns:
        用户信息字典

    Raises:
        HTTPException: 未认证或 Token 无效时
    """
    from src.infrastructure.mysql_client import get_db

    # 获取依赖
    from src.repositories.user_repo import UserRepository
    from src.infrastructure.jwt_handler import get_jwt_handler

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCodes.TOKEN_MISSING[1],
        )

    try:
        db = next(get_db())
        jwt_handler = get_jwt_handler()

        # 验证 Token
        payload = jwt_handler.verify_token(credentials.credentials)

        # 获取用户信息
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(payload.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorCodes.USER_NOT_FOUND[1],
            )

        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorCodes.ACCOUNT_DISABLED[1],
            )

        return {
            "user_id": payload.user_id,
            "username": payload.username,
            "role": payload.role,
            "user": user,
            "db": db,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCodes.TOKEN_INVALID[1],
        ) from e
