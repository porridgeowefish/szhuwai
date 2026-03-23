"""
认证路由
========

提供用户注册、登录、密码管理、手机号绑定等认证相关接口。
"""

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from src.api.config import api_config
from src.api.routes.common import ApiResponse, ErrorCodes, LoginData, UserWithToken, get_current_user
from src.infrastructure.aliyun_sms_client import get_aliyun_sms_client
from src.infrastructure.jwt_handler import get_jwt_handler
from src.infrastructure.mysql_client import get_db
from src.infrastructure.password_hasher import get_password_hasher
from src.repositories.sms_code_repo import SmsCodeRepository
from src.repositories.sms_log_repo import SmsLogRepository
from src.repositories.user_repo import UserRepository
from src.schemas.auth import (
    BindPhoneRequest,
    ChangePasswordRequest,
    PhoneLoginRequest,
    PhoneRegisterRequest,
    ResetPasswordRequest,
    UsernameLoginRequest,
    UsernameRegisterRequest,
)
from src.schemas.user import UserResponse
from src.services.auth_service import AuthService
from src.services.sms_service import SmsService

router = APIRouter(prefix="/auth", tags=["认证"])


# ============ 请求模型 ============
class UnbindPhoneRequest(BaseModel):
    """解绑手机请求"""

    code: str = Field(..., min_length=6, max_length=6, description="验证码")


# ============ 依赖注入 ============
def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    db = next(get_db())
    user_repo = UserRepository(db)

    sms_code_repo = SmsCodeRepository(db)
    sms_log_repo = SmsLogRepository(db)
    sms_client = get_aliyun_sms_client()
    sms_service = SmsService(sms_code_repo, sms_log_repo, sms_client, api_config)

    jwt_handler = get_jwt_handler()
    password_hasher = get_password_hasher()

    return AuthService(user_repo, sms_service, jwt_handler, password_hasher)


# ============ 公开接口 ============


class CheckExistsRequest(BaseModel):
    """检查是否存在请求"""

    username: str | None = Field(default=None, min_length=3, max_length=20, description="用户名")
    phone: str | None = Field(default=None, description="手机号")


class CheckExistsResponse(BaseModel):
    """检查是否存在响应"""

    exists: bool = Field(..., description="是否存在")
    field: str = Field(..., description="检查的字段：username 或 phone")


@router.post("/check-exists", response_model=ApiResponse[CheckExistsResponse])
async def check_exists(
    request: CheckExistsRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ApiResponse[CheckExistsResponse]:
    """
    检查用户名或手机号是否已存在

    用于注册时的实时验证。

    - **username**: 用户名（可选）
    - **phone**: 手机号（可选，至少提供一个）

    返回对应字段是否已存在。
    """
    if request.username:
        exists = auth_service._user_repo.exists_by_username(request.username)
        return ApiResponse[CheckExistsResponse](
            code=200,
            message="检查完成",
            data=CheckExistsResponse(exists=exists, field="username"),
        )
    elif request.phone:
        exists = auth_service._user_repo.exists_by_phone(request.phone)
        return ApiResponse[CheckExistsResponse](
            code=200,
            message="检查完成",
            data=CheckExistsResponse(exists=exists, field="phone"),
        )
    else:
        return ApiResponse[CheckExistsResponse](
            code=400,
            message="请提供 username 或 phone 参数",
            data=None,
        )


@router.post("/register", response_model=ApiResponse[UserWithToken], status_code=status.HTTP_201_CREATED)
async def register_by_username(
    request: UsernameRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ApiResponse[UserWithToken]:
    """
    用户名注册

    使用用户名和密码注册新账号。

    - **username**: 用户名（3-20 字符，字母开头，只能包含字母、数字、下划线）
    - **password**: 密码（6-32 字符）

    注册成功后返回用户信息和访问令牌。
    """
    result = auth_service.register_by_username(request.username, request.password)

    if result is None:
        return ApiResponse[UserWithToken](
            code=ErrorCodes.USER_EXISTS[0],
            message=ErrorCodes.USER_EXISTS[1],
            data=None,
        )

    user_response, token = result

    return ApiResponse[UserWithToken](
        code=200,
        message="注册成功",
        data=UserWithToken(
            user=user_response,
            accessToken=token,
            tokenType="Bearer",
            expiresIn=api_config.JWT_EXPIRE_SECONDS,
        ),
    )


@router.post("/login", response_model=ApiResponse[LoginData])
async def login_by_username(
    request: UsernameLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ApiResponse[LoginData]:
    """
    用户名登录

    使用用户名和密码登录。

    - **username**: 用户名
    - **password**: 密码

    登录成功后返回用户信息和访问令牌。
    """
    result = auth_service.login_by_username(request.username, request.password)

    if not result.success:
        # 映射错误码
        if result.error_code == "USER_NOT_FOUND":
            error_code = ErrorCodes.USER_NOT_FOUND[0]
            error_message = ErrorCodes.USER_NOT_FOUND[1]
        elif result.error_code == "INVALID_PASSWORD":
            error_code = ErrorCodes.INVALID_PASSWORD[0]
            error_message = ErrorCodes.INVALID_PASSWORD[1]
        elif result.error_code == "ACCOUNT_DISABLED":
            error_code = ErrorCodes.ACCOUNT_DISABLED[0]
            error_message = ErrorCodes.ACCOUNT_DISABLED[1]
        else:
            error_code = ErrorCodes.INTERNAL_ERROR[0]
            error_message = result.error_message or "登录失败"

        return ApiResponse[LoginData](
            code=error_code,
            message=error_message,
            data=None,
        )

    return ApiResponse[LoginData](
        code=200,
        message="登录成功",
        data=LoginData(
            accessToken=result.token,  # type: ignore
            tokenType="Bearer",
            expiresIn=api_config.JWT_EXPIRE_SECONDS,
            user=result.user,  # type: ignore
        ),
    )


@router.post("/sms/register", response_model=ApiResponse[UserWithToken], status_code=status.HTTP_201_CREATED)
async def register_by_phone(
    request: PhoneRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ApiResponse[UserWithToken]:
    """
    手机号注册

    使用手机号和验证码注册新账号。

    - **phone**: 手机号（中国大陆 11 位）
    - **code**: 验证码（6 位数字）
    - **password**: 密码（可选，6-32 字符）
    - **username**: 用户名（可选，3-20 字符）

    如果不提供密码，注册后只能使用手机号验证码登录。
    """
    result = auth_service.register_by_phone(request.phone, request.code, request.password, request.username)

    if result is None:
        return ApiResponse[UserWithToken](
            code=ErrorCodes.INVALID_CODE[0],
            message="验证码错误或手机号已注册",
            data=None,
        )

    user_response, token = result

    return ApiResponse[UserWithToken](
        code=200,
        message="注册成功",
        data=UserWithToken(
            user=user_response,
            accessToken=token,
            tokenType="Bearer",
            expiresIn=api_config.JWT_EXPIRE_SECONDS,
        ),
    )


@router.post("/sms/login", response_model=ApiResponse[LoginData])
async def login_by_phone(
    request: PhoneLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ApiResponse[LoginData]:
    """
    手机号登录

    使用手机号和验证码登录。

    - **phone**: 手机号
    - **code**: 验证码（6 位数字）

    登录成功后返回用户信息和访问令牌。
    """
    result = auth_service.login_by_phone(request.phone, request.code)

    if not result.success:
        # 映射错误码
        if result.error_code == "INVALID_CODE":
            error_code = ErrorCodes.INVALID_CODE[0]
            error_message = ErrorCodes.INVALID_CODE[1]
        elif result.error_code == "PHONE_NOT_REGISTERED":
            error_code = ErrorCodes.PHONE_NOT_REGISTERED[0]
            error_message = ErrorCodes.PHONE_NOT_REGISTERED[1]
        elif result.error_code == "ACCOUNT_DISABLED":
            error_code = ErrorCodes.ACCOUNT_DISABLED[0]
            error_message = ErrorCodes.ACCOUNT_DISABLED[1]
        else:
            error_code = ErrorCodes.INTERNAL_ERROR[0]
            error_message = result.error_message or "登录失败"

        return ApiResponse[LoginData](
            code=error_code,
            message=error_message,
            data=None,
        )

    return ApiResponse[LoginData](
        code=200,
        message="登录成功",
        data=LoginData(
            accessToken=result.token,  # type: ignore
            tokenType="Bearer",
            expiresIn=api_config.JWT_EXPIRE_SECONDS,
            user=result.user,  # type: ignore
        ),
    )


@router.post("/password/reset", response_model=ApiResponse[None])
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ApiResponse[None]:
    """
    重置密码

    使用手机号和验证码重置密码。

    - **phone**: 手机号
    - **code**: 验证码（6 位数字）
    - **new_password**: 新密码（6-32 字符）

    需要先通过短信接口获取验证码。
    """
    result = auth_service.reset_password(request.phone, request.code, request.new_password)

    if not result:
        return ApiResponse[None](
            code=ErrorCodes.INVALID_CODE[0],
            message="验证码错误或手机号未注册",
            data=None,
        )

    return ApiResponse[None](
        code=200,
        message="密码重置成功",
        data=None,
    )


# ============ 需要认证的接口 ============


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_info(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ApiResponse[UserResponse]:
    """
    获取当前用户信息

    需要在请求头中提供有效的 Authorization Token。

    返回当前登录用户的详细信息。
    """
    user_response = UserResponse.model_validate(current_user["user"])

    return ApiResponse[UserResponse](
        code=200,
        message="获取成功",
        data=user_response,
    )


@router.post("/phone/bind", response_model=ApiResponse[UserResponse])
async def bind_phone(
    request: BindPhoneRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> ApiResponse[UserResponse]:
    """
    绑定手机号

    为当前账号绑定手机号。

    - **phone**: 手机号（11 位）
    - **code**: 验证码（6 位数字）

    需要先通过短信接口获取验证码。
    """
    user_id = current_user["user_id"]
    result = auth_service.bind_phone(user_id, request.phone, request.code)

    if result is None:
        return ApiResponse[UserResponse](
            code=ErrorCodes.INVALID_CODE[0],
            message="验证码错误或手机号已被绑定",
            data=None,
        )

    return ApiResponse[UserResponse](
        code=200,
        message="绑定成功",
        data=result,
    )


@router.post("/phone/unbind", response_model=ApiResponse[UserResponse])
async def unbind_phone(
    request: UnbindPhoneRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> ApiResponse[UserResponse]:
    """
    解绑手机号

    解除当前账号的手机号绑定。

    - **code**: 验证码（6 位数字）

    需要使用已绑定手机号接收的验证码。
    """
    user_id = current_user["user_id"]
    result = auth_service.unbind_phone(user_id, request.code)

    if result is None:
        return ApiResponse[UserResponse](
            code=ErrorCodes.INVALID_CODE[0],
            message="验证码错误或未绑定手机号",
            data=None,
        )

    return ApiResponse[UserResponse](
        code=200,
        message="解绑成功",
        data=result,
    )


@router.post("/password/change", response_model=ApiResponse[None])
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> ApiResponse[None]:
    """
    修改密码

    修改当前账号的密码。

    - **old_password**: 旧密码
    - **new_password**: 新密码（6-32 字符）

    需要验证旧密码是否正确。
    """
    user_id = current_user["user_id"]
    result = auth_service.change_password(user_id, request.old_password, request.new_password)

    if not result:
        return ApiResponse[None](
            code=ErrorCodes.INVALID_PASSWORD[0],
            message="旧密码错误",
            data=None,
        )

    return ApiResponse[None](
        code=200,
        message="密码修改成功",
        data=None,
    )
