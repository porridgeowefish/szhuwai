"""运行时 API 配置检测接口。"""

from time import perf_counter
from typing import Callable, Literal

import requests
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.api.config import APIConfig
from src.api.map_client import MapClient
from src.api.search_client import SearchClient
from src.api.weather_client import WeatherClient
from src.schemas.runtime_config import RuntimeAPIConfig

router = APIRouter(prefix="/runtime", tags=["运行时配置"])

APIService = Literal["map", "weather", "search", "llm"]
TestStatus = Literal["success", "failed", "skipped"]


class ApiConnectionTestRequest(BaseModel):
    """测试浏览器随请求提供的 API 配置。"""

    service: APIService | Literal["all"] = "all"
    api_config: RuntimeAPIConfig = Field(default_factory=RuntimeAPIConfig)


class ApiConnectionTestResult(BaseModel):
    """单个 API 连通性测试结果。"""

    service: APIService
    label: str
    status: TestStatus
    message: str
    duration_ms: int


class ApiConnectionTestResponse(BaseModel):
    """API 连通性测试响应。"""

    results: list[ApiConnectionTestResult]


@router.post("/test", response_model=ApiConnectionTestResponse)
def test_runtime_api(payload: ApiConnectionTestRequest) -> ApiConnectionTestResponse:
    """对高德、和风天气、搜索和 LLM 做轻量连通性测试。"""

    config = payload.api_config.to_api_config().model_copy(update={
        "TIMEOUT": 8,
        "RETRY": 0,
        "LLM_TIMEOUT": 20,
    })
    services: list[APIService] = (
        ["map", "weather", "search", "llm"]
        if payload.service == "all"
        else [payload.service]
    )

    testers: dict[APIService, tuple[str, Callable[[], None]]] = {
        "map": ("高德地图", lambda: _test_map(config)),
        "weather": ("和风天气", lambda: _test_weather(config)),
        "search": ("网络搜索", lambda: _test_search(config)),
        "llm": ("AI 摘要", lambda: _test_llm(config)),
    }
    results = [_run_test(service, *testers[service]) for service in services]
    return ApiConnectionTestResponse(results=results)


def _run_test(service: APIService, label: str, action: Callable[[], None]) -> ApiConnectionTestResult:
    started = perf_counter()
    try:
        action()
    except ValueError as exc:
        return ApiConnectionTestResult(
            service=service,
            label=label,
            status="skipped",
            message=str(exc),
            duration_ms=_elapsed_ms(started),
        )
    except Exception as exc:  # noqa: BLE001 - 连通性检测需要把第三方错误转成可展示文本
        return ApiConnectionTestResult(
            service=service,
            label=label,
            status="failed",
            message=str(exc)[:300] or "连接失败",
            duration_ms=_elapsed_ms(started),
        )
    return ApiConnectionTestResult(
        service=service,
        label=label,
        status="success",
        message="连接正常",
        duration_ms=_elapsed_ms(started),
    )


def _test_map(config: APIConfig) -> None:
    if not config.MAP_API_KEY:
        raise ValueError("未配置高德地图 API Key")
    MapClient(config).geocode("北京市天安门", city="北京")


def _test_weather(config: APIConfig) -> None:
    if not config.WEATHER_API_KEY:
        raise ValueError("未配置和风天气 API Key")
    WeatherClient(config).get_weather_now("101010100")


def _test_search(config: APIConfig) -> None:
    if not config.SEARCH_API_KEY:
        raise ValueError("未配置搜索 API Key")
    SearchClient(config).search("户外徒步", max_results=1, search_depth="basic", timeout=8)


def _test_llm(config: APIConfig) -> None:
    if not config.LLM_API_KEY:
        raise ValueError("未配置 AI API Key")
    response = requests.post(
        f"{config.LLM_BASE_URL.rstrip('/')}/chat/completions",
        headers=config.get_headers("llm"),
        json={
            "model": config.LLM_MODEL,
            "messages": [
                {"role": "system", "content": "只回复 ok。"},
                {"role": "user", "content": "连接测试"},
            ],
            "temperature": 0,
            "max_tokens": 8,
        },
        timeout=min(config.LLM_TIMEOUT, 20),
        proxies=config.PROXY if config.should_use_proxy() else {"http": None, "https": None},
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("choices"):
        raise RuntimeError("AI 服务未返回 choices")


def _elapsed_ms(started: float) -> int:
    return max(0, round((perf_counter() - started) * 1000))
