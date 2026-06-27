import pytest
from pydantic import ValidationError

from src.api.utils import APIError
from src.schemas.transport import ReverseGeocodeResult
from src.services.transport_service import TransportService


def test_transport_plan_returns_degraded_result_when_map_api_fails(monkeypatch) -> None:
    def fail_geocode(*_args, **_kwargs):
        raise APIError("高德地图 API 错误: INVALID_USER_KEY (infocode=10001)")

    service = TransportService()
    monkeypatch.setattr(service.client, "geocode", fail_geocode)

    result = service.plan("北京大学", "116.391,39.907")

    assert result.outbound == {}
    assert result.destination.lon == 116.391
    assert result.destination.lat == 39.907
    assert result.recommended_mode == "交通接口不可用，需人工确认集合点、停车和返程"
    assert "INVALID_USER_KEY" in (result.summary.cost or "")


def test_search_around_rescue_returns_empty_list_when_map_api_fails(monkeypatch) -> None:
    def fail_search(*_args, **_kwargs):
        raise APIError("高德地图 API 错误: SERVICE_NOT_AVAILABLE (infocode=10020)")

    service = TransportService()
    monkeypatch.setattr(service.client, "search_around", fail_search)

    assert service.search_around_rescue(116.391, 39.907) == []


def test_reverse_geocode_handles_overseas_empty_adcode(monkeypatch) -> None:
    """境外坐标高德返回空 adcode，reverse_geocode 不应抛 ValidationError（回归）"""
    service = TransportService()

    def fake_regeo(*_args, **_kwargs):
        return {"regeocode": {"addressComponent": {}, "formatted_address": "", "pois": [], "roads": []}}

    monkeypatch.setattr(service.client, "_make_request", fake_regeo)
    result = service.client.reverse_geocode("139.650027,35.676423")
    assert result.adcode == ""  # 境外无行政区划码，降级为空，不崩


def test_adcode_validator_still_rejects_malformed() -> None:
    """放宽空值后，非空 adcode 仍要校验为 6/12 位数字"""
    with pytest.raises(ValidationError):
        ReverseGeocodeResult(
            address="x", province="x", city="x", district="x",
            adcode="abc123", lon=116.0, lat=39.9,
        )
