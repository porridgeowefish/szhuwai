"""
API Utilities
=============

Utility functions and classes for API management.
"""

import requests
import time
import logging
from functools import wraps
from typing import Dict, Optional, Callable, Any
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json

from .config import APIConfig


logger = logging.getLogger(__name__)


class RateLimiter:
    """速率限制器"""
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.window_start = datetime.now()

    def wait(self):
        """等待直到可以发送请求"""
        now = datetime.now()

        # 检查时间窗口是否已过
        if (now - self.window_start).total_seconds() > 60:
            # 重置窗口
            self.requests = []
            self.window_start = now

        # 如果请求数达到限制，等待
        if len(self.requests) >= self.requests_per_minute:
            # 计算需要等待的时间
            oldest_request = min(self.requests)
            wait_time = (timedelta(minutes=1) - (now - oldest_request)).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)

            # 重置窗口
            self.requests = []
            self.window_start = now

        # 记录当前请求
        self.requests.append(now)


class APICache:
    """带TTL的内存缓存"""
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.access_times = {}

    def get(self, key: str) -> Optional[Dict]:
        """获取缓存数据"""
        if key in self.cache:
            # 检查是否过期
            if (datetime.now() - self.access_times[key]).total_seconds() < self.ttl:
                # 更新访问时间
                self.access_times[key] = datetime.now()
                return self.cache[key]
            else:
                # 删除过期缓存
                del self.cache[key]
                del self.access_times[key]
        return None

    def set(self, key: str, data: Dict) -> None:
        """设置缓存数据"""
        # 如果缓存已满，删除最旧的项
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]

        # 设置新缓存
        self.cache[key] = data
        self.access_times[key] = datetime.now()

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()

    def get_stats(self) -> Dict:
        """获取缓存统计"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "hit_rate": self.cache.get("hit_rate", 0)
        }


class APIError(Exception):
    """API 基础错误"""
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class RateLimitError(APIError):
    """超出速率限制"""
    pass


class AuthenticationError(APIError):
    """认证失败"""
    pass


class NetworkError(APIError):
    """网络错误"""
    pass


class NotFoundError(APIError):
    """资源未找到"""
    pass


class TimeoutError(APIError):
    """请求超时"""
    pass


def handle_api_errors(func: Callable) -> Callable:
    """API错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.Timeout:
            raise TimeoutError("请求超时", 0, {})
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError("超出速率限制", 429, e.response.json())
            elif e.response.status_code in [401, 403]:
                raise AuthenticationError("认证失败", e.response.status_code, e.response.json())
            elif e.response.status_code == 404:
                raise NotFoundError("资源未找到", 404, e.response.json())
            else:
                raise APIError(f"API错误: {e.response.status_code}", e.response.status_code, e.response.json())
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"网络错误: {str(e)}", 0, {})
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise APIError(f"未知错误: {str(e)}", 0, {})
    return wrapper


class BaseAPIClient(ABC):
    """所有 API 客户端的基类"""

    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(config.RATE_LIMIT)
        self.cache = APICache(
            max_size=config.CACHE_MAX_SIZE,
            ttl=config.CACHE_TTL
        )

    @abstractmethod
    def validate_response(self, response: Dict) -> bool:
        """验证API响应格式"""
        pass

    @abstractmethod
    def parse_error(self, response: Dict) -> str:
        """解析错误信息"""
        pass

    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """生成缓存键"""
        import hashlib
        cache_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def _make_request(self, method: str, endpoint: str, params: Dict = None,
                     data: Dict = None, headers: Dict = None,
                     timeout: int = None) -> Dict:
        """发送HTTP请求"""
        # 检查缓存
        if method.upper() == 'GET':
            cache_key = self._get_cache_key(endpoint, params or {})
            cached_response = self.cache.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for {endpoint}")
                return cached_response

        # 等待速率限制
        self.rate_limiter.wait()

        # 构建URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # 设置请求头
        request_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Outdoor-Agent-Planner/1.0"
        }

        # 添加Accept-Encoding: gzip支持
        request_headers["Accept-Encoding"] = "gzip"

        if headers:
            request_headers.update(headers)

        # 设置代理
        proxies = None
        if self.config.should_use_proxy():
            proxies = self.config.PROXY

        # 设置超时
        request_timeout = timeout or self.config.TIMEOUT

        try:
            # 发送请求
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers,
                proxies=proxies,
                timeout=request_timeout
            )

            # 处理响应
            response.raise_for_status()
            result = response.json()

            # 验证响应
            if not self.validate_response(result):
                raise APIError("Invalid API response format", response.status_code, result)

            # 缓存GET请求
            if method.upper() == 'GET':
                self.cache.set(cache_key, result)

            logger.info(f"API request successful: {method} {endpoint}")
            return result

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.content:
                error_msg = self.parse_error(e.response.json())
            else:
                error_msg = "Unknown error"
            logger.error(f"API request failed: {method} {endpoint} - {error_msg}")
            raise APIError(error_msg, e.response.status_code, e.response.json() if e.response and e.response.content else {})

    def _retry_request(self, func: Callable, *args, **kwargs) -> Any:
        """重试机制"""
        last_exception = None
        for attempt in range(self.config.RETRY + 1):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                last_exception = e
                if attempt < self.config.RETRY:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(f"Retry {attempt + 1}/{self.config.RETRY} after {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed: {str(e)}")
                    raise last_exception
        raise last_exception


def setup_logging(level: str = "INFO") -> None:
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('api_requests.log', encoding='utf-8')
        ]
    )