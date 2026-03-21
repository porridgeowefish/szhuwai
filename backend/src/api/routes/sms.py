"""
短信路由
========

POST /auth/sms/send - 发送短信验证码
"""


from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.api.config import api_config
from src.api.routes.common import ApiResponse, ErrorCodes
from src.infrastructure.mysql_client import get_db
from src.infrastructure.aliyun_sms_client import get_aliyun_sms_client
from src.repositories.sms_code_repo import SmsCodeRepository
from src.repositories.sms_log_repo import SmsLogRepository
from src.schemas.sms import SmsSendRequest
from src.services.sms_service import SmsService

router = APIRouter(prefix="/auth/sms", tags=["短信"])


# ============ 响应模型 ============
class SendCodeData(BaseModel):
    """发送验证码响应数据"""

    expireIn: int = Field(..., description="验证码有效期（秒）")
    cooldown: int = Field(..., description="冷却时间（秒）")


# ============ 依赖注入 ============
def get_sms_service() -> SmsService:
    """获取短信服务实例"""
    db = next(get_db())
    sms_code_repo = SmsCodeRepository(db)
    sms_log_repo = SmsLogRepository(db)
    sms_client = get_aliyun_sms_client()
    return SmsService(sms_code_repo, sms_log_repo, sms_client, api_config)


# ============ 路由定义 ============
@router.post("/send", response_model=ApiResponse[SendCodeData])
async def send_sms_code(
    request: SmsSendRequest,
    http_request: Request,
    sms_service: SmsService = Depends(get_sms_service),
) -> ApiResponse[SendCodeData]:
    """
    发送短信验证码

    向指定手机号发送验证码，支持注册、登录、绑定等场景。

    - **phone**: 手机号（必填）
    - **scene**: 使用场景（register/login/bind/reset_password）
    - **ip**: 请求 IP 地址（可选，用于频率限制）

    返回验证码有效期和冷却时间。
    """
    # 获取客户端 IP
    ip = _get_client_ip(http_request)

    # 发送验证码
    result = sms_service.send_code(request.phone, request.scene, ip)

    if result.success:
        return ApiResponse[SendCodeData](
            code=200,
            message="验证码发送成功",
            data=SendCodeData(expireIn=result.expire_in, cooldown=result.cooldown),
        )

    # 处理错误
    error_code = result.error_code or "UNKNOWN_ERROR"
    error_message = result.error_message or "发送失败"

    # 映射错误码
    if error_code == "INVALID_PHONE":
        mapped_code = ErrorCodes.INVALID_PARAMS[0]
        mapped_message = "手机号格式错误"
    elif error_code == "RATE_LIMITED":
        mapped_code = ErrorCodes.RATE_LIMITED[0]
        mapped_message = error_message
    elif error_code == "DAILY_LIMIT_EXCEEDED":
        mapped_code = ErrorCodes.RATE_LIMITED[0]
        mapped_message = error_message
    else:
        mapped_code = ErrorCodes.INTERNAL_ERROR[0]
        mapped_message = error_message

    return ApiResponse[SendCodeData](
        code=mapped_code,
        message=mapped_message,
        data=None,
    )


def _get_client_ip(request: Request) -> str | None:
    """获取客户端 IP 地址"""
    # 优先从 X-Forwarded-For 获取
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # 其次从 X-Real-IP 获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 最后从 client 获取
    return request.client.host if request.client else None
