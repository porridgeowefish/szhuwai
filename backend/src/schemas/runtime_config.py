"""由浏览器随请求提供的 API 配置。"""

import os

from pydantic import BaseModel, Field

from src.api.config import APIConfig, api_config


class RuntimeAPIConfig(BaseModel):
    """仅用于当前请求，不在服务端持久化。"""

    weather_api_key: str = ""
    weather_developer_host: str = "devapi"
    map_api_key: str = ""
    search_api_key: str = ""
    llm_api_key: str = ""
    llm_base_url: str = "https://api.siliconflow.cn/v1"
    llm_model: str = "Pro/moonshotai/Kimi-K2.5"
    llm_temperature: float = Field(default=0.3, ge=0, le=1)
    llm_max_tokens: int = Field(default=8192, ge=512, le=32768)

    def to_api_config(self) -> APIConfig:
        """合并为 API 客户端配置。

        浏览器随请求显式传来的字段优先生效；字段为空时再使用服务端 ``.env`` 兜底。
        这样设置页的连接测试和生成流程都使用用户当前看到的配置。所有 key 一律 ``.strip()`` 去除首尾空白——
        高德对 key 前后的空格/换行零容忍（返回 INVALID_USER_KEY），而复制粘贴极易
        混入不可见空白。``SEARCH_PROVIDER`` / ``PROXY`` 始终取自服务端。
        """

        return APIConfig(
            WEATHER_API_KEY=(self.weather_api_key or api_config.WEATHER_API_KEY).strip(),
            WEATHER_DEVELOPER_HOST=(
                self.weather_developer_host or os.getenv("WEATHER_DEVELOPER_HOST", "")
            ).strip(),
            MAP_API_KEY=(self.map_api_key or api_config.MAP_API_KEY).strip(),
            SEARCH_API_KEY=(self.search_api_key or api_config.SEARCH_API_KEY).strip(),
            LLM_API_KEY=(self.llm_api_key or api_config.LLM_API_KEY).strip(),
            LLM_BASE_URL=(self.llm_base_url or os.getenv("LLM_BASE_URL", "")).strip().rstrip("/"),
            LLM_MODEL=(self.llm_model or os.getenv("LLM_MODEL", "")).strip(),
            SEARCH_PROVIDER=api_config.SEARCH_PROVIDER,
            PROXY=api_config.PROXY,
            LLM_TEMPERATURE=self.llm_temperature,
            LLM_MAX_TOKENS=self.llm_max_tokens,
        )
