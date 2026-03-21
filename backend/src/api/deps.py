"""
API 依赖注入模块
================

提供 FastAPI 路由的依赖注入函数，包括认证、权限检查等。
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.infrastructure.jwt_handler import TokenPayload, get_jwt_handler
from src.infrastructure.mysql_client import get_db
from src.repositories.user_repo import UserRepository
from src.schemas.user import UserResponse

# ============ Bearer Token 安全方案 ============
security = HTTPBearer(auto_error=False)


# ============ 获取数据库会话 ============
def get_user_repo() -> UserRepository:
    """获取用户仓库实例

    这是一个工厂函数，用于 FastAPI 依赖注入。

    Returns:
        UserRepository: 用户仓库实例
    """
    db: Session = next(get_db())
    return UserRepository(db)


# ============ 认证依赖函数 ============


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> UserResponse:
    """获取当前登录用户

    从 Bearer Token 中解析用户信息，验证 Token 有效性并返回用户数据。

    Args:
        credentials: HTTP Bearer Token 凭证
        user_repo: 用户仓库实例

    Returns:
        UserResponse: 当前登录用户信息

    Raises:
        HTTPException: Token 无效、用户不存在或用户已禁用时抛出 401/403 异常
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401003, "message": "缺少 Authorization 头"},
        )

    token = credentials.credentials

    try:
        # 验证 Token
        jwt_handler = get_jwt_handler()
        payload: TokenPayload = jwt_handler.verify_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401002, "message": "Token 无效或已过期"},
        )

    # 获取用户
    user = user_repo.get_by_id(payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 100001, "message": "用户不存在"},
        )

    # 检查用户状态
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 100007, "message": "账号已被禁用"},
        )

    return UserResponse.model_validate(user)


async def get_current_active_user(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> UserResponse:
    """获取当前活跃用户

    这是 get_current_user 的别名，语义上更清晰。
    要求用户必须处于活跃状态。

    Args:
        current_user: 当前登录用户（由 get_current_user 注入）

    Returns:
        UserResponse: 当前活跃用户信息
    """
    return current_user


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> UserResponse | None:
    """获取可选的当前用户

    尝试从请求头中解析 Token，但不强制要求认证。
    如果 Token 无效或未提供，返回 None。

    Args:
        credentials: HTTP Bearer Token 凭证（可选）
        user_repo: 用户仓库实例

    Returns:
        UserResponse | None: 用户信息，未认证时返回 None
    """
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        # 验证 Token
        jwt_handler = get_jwt_handler()
        payload: TokenPayload = jwt_handler.verify_token(token)
    except Exception:
        return None

    # 获取用户
    user = user_repo.get_by_id(payload.user_id)
    if not user or user.status != "active":
        return None

    return UserResponse.model_validate(user)


async def get_admin_user(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> UserResponse:
    """获取管理员用户

    验证当前用户是否为管理员，非管理员用户会收到 403 错误。

    Args:
        current_user: 当前登录用户（由 get_current_user 注入）

    Returns:
        UserResponse: 管理员用户信息

    Raises:
        HTTPException: 非管理员用户抛出 403 异常
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 403002, "message": "需要管理员权限"},
        )
    return current_user


# ============ 类型别名（简化使用） ============
# 使用方式: @router.get("/me") async def get_me(user: CurrentUser)
CurrentUser = Annotated[UserResponse, Depends(get_current_user)]

# 使用方式: @router.get("/admin/users") async def list_users(admin: AdminUser)
AdminUser = Annotated[UserResponse, Depends(get_admin_user)]

# 使用方式: @router.get("/profile") async def get_profile(user: OptionalUser)
OptionalUser = Annotated[UserResponse | None, Depends(get_optional_user)]
