"""运行时 API 配置合并测试。"""

from src.api.config import APIConfig
from src.schemas.runtime_config import RuntimeAPIConfig


def test_runtime_config_prefers_explicit_browser_values(monkeypatch) -> None:
    """设置页显式传来的配置应优先于服务端旧环境配置。"""
    monkeypatch.setattr(
        "src.schemas.runtime_config.api_config",
        APIConfig(
            MAP_API_KEY="server-map",
            WEATHER_API_KEY="server-weather",
            SEARCH_API_KEY="server-search",
            LLM_API_KEY="server-llm",
            LLM_BASE_URL="https://server.example.com/v1",
            LLM_MODEL="server-model",
        ),
    )

    config = RuntimeAPIConfig(
        map_api_key="browser-map",
        weather_api_key="browser-weather",
        search_api_key="browser-search",
        llm_api_key="browser-llm",
        llm_base_url="https://browser.example.com/v1",
        llm_model="browser-model",
    ).to_api_config()

    assert config.MAP_API_KEY == "browser-map"
    assert config.WEATHER_API_KEY == "browser-weather"
    assert config.SEARCH_API_KEY == "browser-search"
    assert config.LLM_API_KEY == "browser-llm"
    assert config.LLM_BASE_URL == "https://browser.example.com/v1"
    assert config.LLM_MODEL == "browser-model"


def test_runtime_config_falls_back_to_server_values(monkeypatch) -> None:
    """浏览器字段为空时仍可使用服务端环境配置兜底。"""
    monkeypatch.setattr(
        "src.schemas.runtime_config.api_config",
        APIConfig(MAP_API_KEY="server-map", LLM_API_KEY="server-llm"),
    )

    config = RuntimeAPIConfig(map_api_key="", llm_api_key="").to_api_config()

    assert config.MAP_API_KEY == "server-map"
    assert config.LLM_API_KEY == "server-llm"
