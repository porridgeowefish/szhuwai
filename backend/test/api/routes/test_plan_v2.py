"""V2 策划生成接口测试。"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.config import APIConfig
from src.services.two_bulu_browser_service import session_manager
from src.services.two_bulu_service import TwoBuluService

from ._sse import parse_sse_event


def test_generate_plan_returns_quick_plan_without_optional_api_keys(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    track_path = Path(__file__).parents[3] / "test_data" / "test.gpx"

    monkeypatch.setattr(TwoBuluService, "extract_track_id", staticmethod(lambda _url: "demo"))
    monkeypatch.setattr(
        session_manager,
        "get_download_path",
        lambda _session_id, expected_track_id=None: track_path,
    )
    # 默认 .env 会注入真实 key；此处把服务端 api_config 置空，并清掉搜索相关 env，
    # 真实模拟"前后端都没配 key"的降级路径（不触发任何真实外部请求）
    monkeypatch.setattr("src.schemas.runtime_config.api_config", APIConfig())
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("JINA_API_KEY", raising=False)
    monkeypatch.delenv("SEARCH_API_KEY", raising=False)

    response = client.post(
        "/api/v1/plan/generate",
        json={
            "two_bulu_url": "https://www.2bulu.com/track/t-demo.htm",
            "two_bulu_session_id": "session-demo",
            "trip_date": "2026-07-01",
            "departure_point": "北京市海淀区",
            "additional_info": "社团新手较多",
            "api_config": {},
        },
    )

    assert response.status_code == 200
    data = parse_sse_event(response.text, "result")
    assert data["mode"] == "quick_plan"
    assert data["plan"]["planName"]
    assert data["plan"]["trackDetail"]["totalDistanceKm"] > 0
    assert data["run_report"]["run_id"].startswith("run_")
    assert any(stage["stage"] == "quick_synthesis" for stage in data["run_report"]["stages"])
    assert any("天气 API Key" in warning for warning in data["run_report"]["warnings"])
