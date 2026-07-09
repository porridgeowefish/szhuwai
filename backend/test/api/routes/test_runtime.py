"""运行时 API 配置检测接口测试。"""

from fastapi.testclient import TestClient
import pytest

from src.api.config import APIConfig


@pytest.fixture(autouse=True)
def _empty_server_api_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.schemas.runtime_config.api_config", APIConfig())
    monkeypatch.delenv("WEATHER_DEVELOPER_HOST", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)


def test_runtime_test_skips_unconfigured_apis(client: TestClient) -> None:
    response = client.post(
        "/api/v1/runtime/test",
        json={"service": "all", "api_config": {}},
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["service"] for item in data["results"]] == ["map", "weather", "search", "llm"]
    assert all(item["status"] == "skipped" for item in data["results"])


def test_runtime_test_map_uses_runtime_key(client: TestClient, mocker) -> None:
    geocode = mocker.patch("src.api.routes.runtime.MapClient.geocode", return_value=object())

    response = client.post(
        "/api/v1/runtime/test",
        json={"service": "map", "api_config": {"map_api_key": "amap-test-key"}},
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["service"] == "map"
    assert result["status"] == "success"
    geocode.assert_called_once_with("北京市天安门", city="北京")


def test_runtime_test_llm_posts_to_configured_base_url(client: TestClient, mocker) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, list[dict[str, object]]]:
            return {"choices": [{"message": {"content": "ok"}}]}

    post = mocker.patch("src.api.routes.runtime.requests.post", return_value=FakeResponse())

    response = client.post(
        "/api/v1/runtime/test",
        json={
            "service": "llm",
            "api_config": {
                "llm_api_key": "llm-test-key",
                "llm_base_url": "https://llm.example.com/v1",
                "llm_model": "test-model",
            },
        },
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["service"] == "llm"
    assert result["status"] == "success"
    args, kwargs = post.call_args
    assert args[0] == "https://llm.example.com/v1/chat/completions"
    assert kwargs["json"]["model"] == "test-model"
    assert kwargs["headers"]["Authorization"] == "Bearer llm-test-key"
