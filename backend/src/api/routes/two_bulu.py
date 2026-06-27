"""两步路线路与浏览器授权接口。"""

from fastapi import APIRouter, HTTPException, status

from src.schemas.two_bulu import (
    TwoBuluInspectRequest,
    TwoBuluSessionCreateRequest,
    TwoBuluSessionStatus,
    TwoBuluTrackInfo,
)
from src.services.two_bulu_browser_service import (
    BrowserUnavailableError,
    session_manager,
)
from src.services.two_bulu_service import TwoBuluError, TwoBuluService

router = APIRouter(prefix="/two-bulu", tags=["两步路轨迹"])


@router.post("/inspect", response_model=TwoBuluTrackInfo)
def inspect_track(payload: TwoBuluInspectRequest) -> TwoBuluTrackInfo:
    """解析线路 URL，不把线路二维码误当作下载授权。"""

    try:
        return TwoBuluService().inspect(str(payload.url))
    except TwoBuluError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/sessions",
    response_model=TwoBuluSessionStatus,
    status_code=status.HTTP_201_CREATED,
)
def create_session(payload: TwoBuluSessionCreateRequest) -> TwoBuluSessionStatus:
    """打开本机可见浏览器，等待用户扫码登录和手动验证码。"""

    try:
        return session_manager.create(str(payload.url))
    except TwoBuluError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (BrowserUnavailableError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/sessions/{session_id}", response_model=TwoBuluSessionStatus)
def get_session(session_id: str) -> TwoBuluSessionStatus:
    """查询浏览器授权与下载进度。"""

    try:
        return session_manager.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
