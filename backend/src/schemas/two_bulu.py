"""两步路线路与浏览器授权模型。"""

from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class TwoBuluInspectRequest(BaseModel):
    """检查两步路线路 URL。"""

    url: HttpUrl = Field(description="两步路线路页面 URL")


class TwoBuluTrackInfo(BaseModel):
    """从线路 URL 可稳定提取的信息。"""

    source_url: str
    track_id: str
    authorization_required: bool = True
    message: str


class TwoBuluSessionState(str, Enum):
    """浏览器授权会话状态。"""

    STARTING = "starting"
    WAITING_LOGIN = "waiting_login"
    WAITING_CAPTCHA = "waiting_captcha"
    DOWNLOADING = "downloading"
    READY = "ready"
    FAILED = "failed"


class TwoBuluSessionCreateRequest(BaseModel):
    """创建本地浏览器授权会话。"""

    url: HttpUrl = Field(description="两步路线路页面 URL")


class TwoBuluSessionStatus(BaseModel):
    """浏览器授权与轨迹下载进度。"""

    session_id: str
    track_id: str
    state: TwoBuluSessionState
    message: str
    file_name: str | None = None
