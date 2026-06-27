"""由浏览器随请求提供的 API 配置。"""

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

        服务端 ``.env`` 为权威来源（运维托管的真实密钥）；浏览器随请求传来的字段
        仅用于填补 ``.env`` 未配置的空缺。所有 key 一律 ``.strip()`` 去除首尾空白——
        高德对 key 前后的空格/换行零容忍（返回 INVALID_USER_KEY），而复制粘贴极易
        混入不可见空白。``SEARCH_PROVIDER`` / ``PROXY`` 始终取自服务端。
        """

        return APIConfig(
            WEATHER_API_KEY=(api_config.WEATHER_API_KEY or self.weather_api_key).strip(),
            WEATHER_DEVELOPER_HOST=(api_config.WEATHER_DEVELOPER_HOST or self.weather_developer_host).strip(),
            MAP_API_KEY=(api_config.MAP_API_KEY or self.map_api_key).strip(),
            SEARCH_API_KEY=(api_config.SEARCH_API_KEY or self.search_api_key).strip(),
            LLM_API_KEY=(api_config.LLM_API_KEY or self.llm_api_key).strip(),
            LLM_BASE_URL=(api_config.LLM_BASE_URL or self.llm_base_url).strip().rstrip("/"),
            LLM_MODEL=(api_config.LLM_MODEL or self.llm_model).strip(),
            SEARCH_PROVIDER=api_config.SEARCH_PROVIDER,
            PROXY=api_config.PROXY,
            LLM_TEMPERATURE=self.llm_temperature,
            LLM_MAX_TOKENS=self.llm_max_tokens,
        )
