"""外部 API 客户端配置。"""

import os
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field

# 启动即加载 .env：main.py 不会调用 load_dotenv，若不在此加载，本地运行时
# AMAP_API_KEY 等为空 → 高德返回 INVALID_USER_KEY。必须在 from_env() 之前执行。
# override=False：不覆盖容器/系统已注入的环境变量（Docker 场景仍以注入值为准）。
try:  # pragma: no cover - 依赖可选，缺失时降级为读系统环境变量
    from dotenv import load_dotenv

    load_dotenv(override=False)
except ImportError:
    pass


class APIConfig(BaseModel):
    """核心策划流程使用的请求配置。"""

    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    WEATHER_API_KEY: str = ""
    WEATHER_DEVELOPER_HOST: str = "devapi"
    MAP_API_KEY: str = ""
    # 搜索服务商：tavily（默认，配置页即此项、有免费额度）或 jina（免费但需另申请 jina_ key、国内需代理）
    SEARCH_PROVIDER: str = "tavily"
    SEARCH_API_KEY: str = ""
    LLM_API_KEY: str = ""

    WEATHER_BASE_URL: str = "https://devapi.qweatherapi.com/v7"
    MAP_BASE_URL: str = "https://restapi.amap.com/v3"
    SEARCH_BASE_URL: str = "https://api.tavily.com"
    LLM_BASE_URL: str = "https://api.siliconflow.cn/v1"
    LLM_MODEL: str = "Pro/moonshotai/Kimi-K2.5"

    TIMEOUT: int = Field(default=10, ge=1)
    RETRY: int = Field(default=3, ge=0, le=5)
    RATE_LIMIT: int = Field(default=30, ge=1)
    CACHE_TTL: int = Field(default=3600, ge=0)
    CACHE_MAX_SIZE: int = Field(default=1000, ge=1)
    LLM_TEMPERATURE: float = Field(default=0.3, ge=0, le=1)
    LLM_MAX_TOKENS: int = Field(default=8192, ge=512)
    LLM_TIMEOUT: int = Field(default=600, ge=10)
    PROXY: Dict[str, str] = Field(default_factory=dict)

    def should_use_proxy(self) -> bool:
        return bool(self.PROXY.get("http") or self.PROXY.get("https"))

    def get_headers(self, api_type: str = "default") -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Outdoor-Agent-Planner/1.0",
        }
        if api_type == "search":
            headers["Authorization"] = f"Bearer {self.SEARCH_API_KEY}"
        elif api_type == "llm":
            headers["Authorization"] = f"Bearer {self.LLM_API_KEY}"
        return headers

    def get_cache_key(self, api_type: str, params: Dict[str, Any]) -> str:
        import json

        return f"{api_type}:{json.dumps(sorted(params.items()), ensure_ascii=False)}"

    @classmethod
    def from_env(cls) -> "APIConfig":
        provider = (os.getenv("SEARCH_PROVIDER", "tavily") or "tavily").strip().lower()

        # 代理：国内访问 Jina 等海外搜索服务时必需。PROXY_HTTP/PROXY_HTTPS → requests 代理字典。
        proxy: Dict[str, str] = {}
        proxy_http = os.getenv("PROXY_HTTP", "")
        proxy_https = os.getenv("PROXY_HTTPS", "")
        if proxy_http:
            proxy["http"] = proxy_http
        if proxy_https:
            proxy["https"] = proxy_https

        # 搜索 key 按服务商取对应变量，避免把 Tavily 的 key 误当作 Jina key 发出去。
        search_key = os.getenv("SEARCH_API_KEY", "")
        if not search_key:
            search_key = (
                os.getenv("TAVILY_API_KEY", "")
                if provider == "tavily"
                else os.getenv("JINA_API_KEY", "")
            )

        return cls(
            WEATHER_API_KEY=os.getenv("QWEATHER_API_KEY", ""),
            WEATHER_DEVELOPER_HOST=os.getenv("WEATHER_DEVELOPER_HOST", "devapi"),
            MAP_API_KEY=os.getenv("AMAP_API_KEY", ""),
            SEARCH_PROVIDER=provider,
            SEARCH_API_KEY=search_key,
            LLM_API_KEY=os.getenv("LLM_API_KEY", ""),
            LLM_BASE_URL=os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1"),
            LLM_MODEL=os.getenv("LLM_MODEL", "Pro/moonshotai/Kimi-K2.5"),
            PROXY=proxy,
        )


api_config = APIConfig.from_env()
