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
        default={},
        description="代理服务器配置"
    )

    # 缓存配置
    CACHE_TTL: int = Field(default=3600, description="缓存有效期（秒）")
    CACHE_MAX_SIZE: int = Field(default=1000, description="缓存最大条目数")

    # API 端点
    WEATHER_BASE_URL: str = Field(
        default="https://devapi.qweatherapi.com/v7",
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
        default="https://api.siliconflow.cn/v1/chat/completions",
        description="大模型API基础URL"
    )

    # LLM 配置
    LLM_MODEL: str = Field(
        default="Pro/moonshotai/Kimi-K2.5",
        description="大模型名称"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM 温度参数"
    )
    LLM_MAX_TOKENS: int = Field(
        default=8192,
        ge=1,
        description="LLM 最大输出 token 数"
    )
    LLM_TIMEOUT: int = Field(
        default=600,
        ge=10,
        description="LLM API 超时时间（秒）"
    )

    # MySQL 配置
    MYSQL_HOST: str = Field(
        default="localhost",
        description="MySQL 主机"
    )
    MYSQL_PORT: int = Field(
        default=3306,
        ge=1,
        le=65535,
        description="MySQL 端口"
    )
    MYSQL_USER: str = Field(
        default="root",
        description="MySQL 用户名"
    )
    MYSQL_PASSWORD: str = Field(
        default="",
        description="MySQL 密码"
    )
    MYSQL_DATABASE: str = Field(
        default="outdoor_planner",
        description="数据库名"
    )
    MYSQL_POOL_SIZE: int = Field(
        default=5,
        ge=1,
        le=100,
        description="连接池大小"
    )

    # MongoDB 配置
    MONGO_HOST: str = Field(
        default="localhost",
        description="MongoDB 主机"
    )
    MONGO_PORT: int = Field(
        default=27017,
        ge=1,
        le=65535,
        description="MongoDB 端口"
    )
    MONGO_USER: str = Field(
        default="",
        description="MongoDB 用户名"
    )
    MONGO_PASSWORD: str = Field(
        default="",
        description="MongoDB 密码"
    )
    MONGO_DATABASE: str = Field(
        default="outdoor_planner",
        description="数据库名"
    )

    # JWT 配置
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="JWT 签名密钥"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT 签名算法"
    )
    JWT_EXPIRE_SECONDS: int = Field(
        default=86400,  # 24小时
        ge=1,
        description="Token 有效期（秒）"
    )

    # 阿里云短信配置
    ALIYUN_ACCESS_KEY_ID: str = Field(
        default="",
        description="阿里云 AccessKey ID"
    )
    ALIYUN_ACCESS_KEY_SECRET: str = Field(
        default="",
        description="阿里云 AccessKey Secret"
    )
    SMS_SIGN_NAME: str = Field(
        default="户外规划助手",
        description="短信签名"
    )
    SMS_TEMPLATE_REGISTER: str = Field(
        default="",
        description="注册短信模板 ID"
    )
    SMS_TEMPLATE_LOGIN: str = Field(
        default="",
        description="登录短信模板 ID"
    )
    SMS_TEMPLATE_BIND: str = Field(
        default="",
        description="绑定手机短信模板 ID"
    )
    SMS_TEMPLATE_UNBIND: str = Field(
        default="",
        description="解绑手机短信模板 ID"
    )
    SMS_TEMPLATE_RESET_PASSWORD: str = Field(
        default="",
        description="重置密码短信模板 ID"
    )
    # 短信业务配置
    SMS_CODE_LENGTH: int = Field(
        default=6,
        ge=4,
        le=8,
        description="验证码长度"
    )
    SMS_EXPIRE_SECONDS: int = Field(
        default=300,  # 5分钟
        ge=60,
        description="验证码有效期（秒）"
    )
    SMS_COOLDOWN_SECONDS: int = Field(
        default=60,  # 60秒
        ge=10,
        description="发送冷却时间（秒）"
    )
    SMS_DAILY_LIMIT: int = Field(
        default=10,
        ge=1,
        description="每日发送上限"
    )

    @field_validator(
        'TIMEOUT', 'RETRY', 'RATE_LIMIT', 'CACHE_TTL', 'CACHE_MAX_SIZE',
        'MYSQL_POOL_SIZE', 'MONGO_PORT'
    )
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
        """从环境文件加载配置

        智能查找 .env 文件：
        1. 优先从环境变量加载（Docker/云端部署方式）
        2. 查找当前目录的 .env
        3. 向上查找父目录的 .env（支持从 backend/ 目录运行）
        """
        # 优先从环境变量加载
        config_data = {}

        # 加载环境变量
        env_mapping = {
            "QWEATHER_API_KEY": "WEATHER_API_KEY",
            "AMAP_API_KEY": "MAP_API_KEY",
            "LLM_API_KEY": "LLM_API_KEY",
            "TAVILY_API_KEY": "SEARCH_API_KEY",
            "WEATHER_DEVELOPER_HOST": "WEATHER_DEVELOPER_HOST",
            # MySQL 环境变量
            "MYSQL_HOST": "MYSQL_HOST",
            "MYSQL_PORT": "MYSQL_PORT",
            "MYSQL_USER": "MYSQL_USER",
            "MYSQL_PASSWORD": "MYSQL_PASSWORD",
            "MYSQL_DATABASE": "MYSQL_DATABASE",
            "MYSQL_POOL_SIZE": "MYSQL_POOL_SIZE",
            # MongoDB 环境变量
            "MONGO_HOST": "MONGO_HOST",
            "MONGO_PORT": "MONGO_PORT",
            "MONGO_USER": "MONGO_USER",
            "MONGO_PASSWORD": "MONGO_PASSWORD",
            "MONGO_DATABASE": "MONGO_DATABASE",
            # 阿里云短信环境变量
            "ALIYUN_ACCESS_KEY_ID": "ALIYUN_ACCESS_KEY_ID",
            "ALIYUN_ACCESS_KEY_SECRET": "ALIYUN_ACCESS_KEY_SECRET",
            "SMS_SIGN_NAME": "SMS_SIGN_NAME",
            "SMS_TEMPLATE_REGISTER": "SMS_TEMPLATE_REGISTER",
            "SMS_TEMPLATE_LOGIN": "SMS_TEMPLATE_LOGIN",
            "SMS_TEMPLATE_BIND": "SMS_TEMPLATE_BIND",
            "SMS_TEMPLATE_UNBIND": "SMS_TEMPLATE_UNBIND",
            "SMS_TEMPLATE_RESET_PASSWORD": "SMS_TEMPLATE_RESET_PASSWORD",
        }

        for env_var, config_key in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value:
                config_data[config_key] = env_value

        # 智能查找 .env 文件路径
        env_path = cls._find_env_file(env_file)

        # 如果.env文件存在，加载它
        if env_path and os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # 处理环境变量映射
                            if key in env_mapping:
                                # 环境变量优先于文件配置
                                if env_mapping[key] not in config_data:
                                    config_data[env_mapping[key]] = value
                            # 处理代理配置
                            elif key == 'PROXY_HTTP':
                                if 'PROXY' not in config_data:
                                    config_data['PROXY'] = {}
                                config_data['PROXY']['http'] = value
                            elif key == 'PROXY_HTTPS':
                                if 'PROXY' not in config_data:
                                    config_data['PROXY'] = {}
                                config_data['PROXY']['https'] = value
                            # 处理其他配置项
                            elif key in cls.model_fields and key not in config_data:
                                config_data[key] = value

        return cls(**config_data)

    @classmethod
    def _find_env_file(cls, env_file: str = ".env") -> str | None:
        """智能查找 .env 文件

        查找顺序：
        1. 当前工作目录
        2. 当前脚本所在目录
        3. 向上逐级查找父目录（最多 5 层）
        """
        # 1. 当前工作目录
        if os.path.exists(env_file):
            return env_file

        # 2. 当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_env = os.path.join(script_dir, env_file)
        if os.path.exists(script_env):
            return script_env

        # 3. 向上查找父目录
        current_dir = os.getcwd()
        for _ in range(5):  # 最多向上查找 5 层
            parent_env = os.path.join(current_dir, env_file)
            if os.path.exists(parent_env):
                return parent_env
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # 已到达根目录
                break
            current_dir = parent_dir

        return None

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
