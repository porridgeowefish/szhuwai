"""
API Configuration
================

Centralized configuration management for all API clients.
"""

import os
from typing import Dict

from pydantic import BaseModel, Field, field_validator, ConfigDict


class APIConfig(BaseModel):
    """API 配置基类"""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="ignore"
    )

    # API 密钥环境变量
    WEATHER_API_KEY: str = Field(
        default="",
        description="和风天气API密钥"
    )
    MAP_API_KEY: str = Field(
        default="",
        description="高德地图API密钥"
    )
    LLM_API_KEY: str = Field(
        default="",
        description="大模型API密钥"
    )
    SEARCH_API_KEY: str = Field(
        default="",
        description="Tavily搜索API密钥"
    )

    # 统一基础配置
    TIMEOUT: int = Field(default=10, description="请求超时时间（秒）")
    RETRY: int = Field(default=3, description="重试次数")
    RATE_LIMIT: int = Field(default=30, description="每分钟请求次数限制")

    # 代理配置
    PROXY: Dict[str, str] = Field(
        default={
            "http": "http://127.0.0.1:7890",
            "https": "http://127.0.0.1:7890"
        },
        description="代理服务器配置"
    )

    # 缓存配置
    CACHE_TTL: int = Field(default=3600, description="缓存有效期（秒）")
    CACHE_MAX_SIZE: int = Field(default=1000, description="缓存最大条目数")

    # API 端点
    WEATHER_BASE_URL: str = Field(
        default="https://api.qweather.com/v7",
        description="和风天气API基础URL"
    )
    WEATHER_DEVELOPER_HOST: str = Field(
        default="devapi",
        description="和风天气开发者主机"
    )
    MAP_BASE_URL: str = Field(
        default="https://restapi.amap.com/v3",
        description="高德地图API基础URL"
    )
    SEARCH_BASE_URL: str = Field(
        default="https://api.tavily.com",
        description="Tavily搜索API基础URL"
    )
    LLM_BASE_URL: str = Field(
        default="https://api.openai.com/v1",
        description="大模型API基础URL"
    )

    @field_validator('TIMEOUT', 'RETRY', 'RATE_LIMIT', 'CACHE_TTL', 'CACHE_MAX_SIZE')
    @classmethod
    def validate_positive_numbers(cls, v: int) -> int:
        """验证数值必须为正数"""
        if v <= 0:
            raise ValueError("配置值必须为正数")
        return v

    def should_use_proxy(self) -> bool:
        """判断是否需要使用代理"""
        # 检查代理配置是否有效
        if self.PROXY:
            return bool(self.PROXY.get('http') or self.PROXY.get('https'))
        return False

    def get_headers(self, api_type: str = "default") -> Dict[str, str]:
        """获取API请求头"""
        base_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Outdoor-Agent-Planner/1.0"
        }

        if api_type == "weather":
            base_headers["X-QWeather-Client"] = f"OutdoorAgent/{self.WEATHER_API_KEY[:8]}"
        elif api_type == "map":
            base_headers["X-Amap-Key"] = self.MAP_API_KEY
        elif api_type == "search":
            base_headers["Authorization"] = f"Bearer {self.SEARCH_API_KEY}"
        elif api_type == "llm":
            base_headers["Authorization"] = f"Bearer {self.LLM_API_KEY}"

        return base_headers

    @classmethod
    def from_env(cls, env_file: str = ".env") -> "APIConfig":
        """从环境文件加载配置"""
        # 优先从环境变量加载
        config_data = {}

        # 加载环境变量
        env_mapping = {
            "QWEATHER_API_KEY": "WEATHER_API_KEY",
            "AMAP_API_KEY": "MAP_API_KEY",
            "LLM_API_KEY": "LLM_API_KEY",
            "TAVILY_API_KEY": "SEARCH_API_KEY"
        }

        for env_var, config_key in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value:
                config_data[config_key] = env_value

        # 如果.env文件存在，加载它
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config_data[key.strip()] = value.strip()

        return cls(**config_data)

    def get_cache_key(self, api_type: str, params: Dict) -> str:
        """生成缓存键"""
        import json
        key_data = {
            "api_type": api_type,
            "params": sorted(params.items())
        }
        return f"{api_type}:{json.dumps(key_data, sort_keys=True)}"


# 全局配置实例
api_config = APIConfig.from_env()
