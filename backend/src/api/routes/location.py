"""定位与地址反查接口。"""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.api.map_client import MapClient
from src.api.utils import APIError
from src.schemas.runtime_config import RuntimeAPIConfig

router = APIRouter(prefix="/location", tags=["定位"])


class LocationResolveRequest(BaseModel):
    """浏览器定位后的地址解析请求。"""

    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    api_config: RuntimeAPIConfig = Field(default_factory=RuntimeAPIConfig)


class LocationResolveResponse(BaseModel):
    """定位解析结果。"""

    success: bool
    source: Literal["reverse_geocode", "ip", "none"]
    address: str | None = None
    coordinate_text: str | None = None
    province: str | None = None
    city: str | None = None
    district: str | None = None
    message: str


@router.post("/resolve", response_model=LocationResolveResponse)
def resolve_location(payload: LocationResolveRequest) -> LocationResolveResponse:
    """优先按经纬度逆地理解析；没有坐标或解析失败时，用 IP 定位兜底。"""

    api_client_config = payload.api_config.to_api_config()
    if not api_client_config.MAP_API_KEY:
        return LocationResolveResponse(
            success=False,
            source="none",
            coordinate_text=_coordinate_text(payload.longitude, payload.latitude),
            message="未配置高德地图 API Key，无法自动解析地址。",
        )

    client = MapClient(api_client_config)  # type: ignore[no-untyped-call]
    coordinate_text = _coordinate_text(payload.longitude, payload.latitude)

    if coordinate_text:
        try:
            result = client.reverse_geocode(coordinate_text)
            return LocationResolveResponse(
                success=True,
                source="reverse_geocode",
                address=result.address,
                coordinate_text=coordinate_text,
                province=result.province,
                city=result.city,
                district=result.district,
                message="已根据浏览器经纬度解析地址。",
            )
        except APIError as exc:
            ip_result = _resolve_by_ip(client)
            if ip_result.success:
                ip_result.coordinate_text = coordinate_text
                ip_result.message = f"坐标反查失败，已使用 IP 定位兜底：{exc}"
                return ip_result
            return LocationResolveResponse(
                success=False,
                source="none",
                coordinate_text=coordinate_text,
                message=f"坐标反查失败：{exc}",
            )

    return _resolve_by_ip(client)


def _resolve_by_ip(client: MapClient) -> LocationResolveResponse:
    try:
        result = client.ip_location()
    except APIError as exc:
        return LocationResolveResponse(
            success=False,
            source="none",
            message=f"IP 定位失败：{exc}",
        )

    province = result.get("province") or ""
    city = result.get("city") or ""
    address = city or province
    if not address:
        return LocationResolveResponse(
            success=False,
            source="none",
            message="高德 IP 定位未返回城市信息。",
        )

    return LocationResolveResponse(
        success=True,
        source="ip",
        address=address,
        province=province or None,
        city=city or None,
        message="浏览器定位不可用，已使用 IP 定位兜底。",
    )


def _coordinate_text(longitude: float | None, latitude: float | None) -> str | None:
    if longitude is None or latitude is None:
        return None
    return f"{longitude:.6f},{latitude:.6f}"
