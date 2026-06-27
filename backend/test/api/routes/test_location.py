"""定位接口测试。"""

from fastapi.testclient import TestClient

from src.api.config import APIConfig


def test_location_resolve_requires_map_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("src.schemas.runtime_config.api_config", APIConfig())

    response = client.post(
        "/api/v1/location/resolve",
        json={
            "longitude": 116.397,
            "latitude": 39.908,
            "api_config": {},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["source"] == "none"
    assert "高德地图 API Key" in data["message"]
    assert data["coordinate_text"] == "116.397000,39.908000"


def test_location_resolve_reverse_geocode(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("src.schemas.runtime_config.api_config", APIConfig())

    class FakeReverseResult:
        address = "北京市东城区天安门"
        province = "北京市"
        city = "北京市"
        district = "东城区"

    monkeypatch.setattr("src.api.routes.location.MapClient.reverse_geocode", lambda *_args, **_kwargs: FakeReverseResult())

    response = client.post(
        "/api/v1/location/resolve",
        json={
            "longitude": 116.397,
            "latitude": 39.908,
            "api_config": {"map_api_key": "demo-key"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["source"] == "reverse_geocode"
    assert data["address"] == "北京市东城区天安门"


def test_location_resolve_ip_fallback(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("src.schemas.runtime_config.api_config", APIConfig())
    monkeypatch.setattr(
        "src.api.routes.location.MapClient.ip_location",
        lambda *_args, **_kwargs: {"province": "广东省", "city": "深圳市", "adcode": "440300"},
    )

    response = client.post(
        "/api/v1/location/resolve",
        json={
            "api_config": {"map_api_key": "demo-key"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["source"] == "ip"
    assert data["address"] == "深圳市"
