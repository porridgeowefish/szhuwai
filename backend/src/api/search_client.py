"""
Search API Client
=================

Provider-aware web search client. 把不同搜索后端（Jina s.jina.ai / Tavily）
的响应统一归一到 :class:`WebSearchResponse`，保证上层字段一致、不因服务商差异崩盘。

- **Tavily**（默认）：``topic`` 区分通用/新闻，``include_raw_content`` 取正文，有免费额度。
- **Jina s.jina.ai**（可选）：免费但需 ``jina_`` key，国内需走代理；无有效 Jina key 时
  若环境存在 Tavily key 会自动降级到 Tavily，避免搜索必挂。
"""

import logging
import os
from typing import Dict, List, Optional
from urllib.parse import urlparse

from . import BaseAPIClient, handle_api_errors
from .config import api_config, APIConfig
from src.schemas.search import SearchResult, SourceType, WebSearchResponse

logger = logging.getLogger(__name__)

# 服务商 → 基础 URL
_PROVIDER_BASE_URL: Dict[str, str] = {
    "jina": "https://s.jina.ai",
    "tavily": "https://api.tavily.com",
}


class SearchClient(BaseAPIClient):
    """搜索 API 客户端（按 ``SEARCH_PROVIDER`` 分派，统一归一到 WebSearchResponse）。"""

    def __init__(self, config: Optional[APIConfig] = None) -> None:
        super().__init__(config or api_config)
        provider = (self.config.SEARCH_PROVIDER or "tavily").strip().lower()
        search_key = (self.config.SEARCH_API_KEY or "").strip()

        # 自动降级：Jina 现已强制要求 API key（无 key 直接 401）。若选了 Jina 却没有
        # 有效的 Jina key（以 jina_ 开头），而环境里存在 Tavily key，则改用 Tavily，
        # 避免搜索必挂。后续配了 Jina key 即自动恢复使用 Jina。
        if provider == "jina" and not search_key.startswith("jina_"):
            tavily_key = (os.getenv("TAVILY_API_KEY", "") or "").strip()
            if tavily_key:
                logger.info("未配置有效的 Jina key，检测到 Tavily key，搜索自动降级到 tavily")
                provider, search_key = "tavily", tavily_key

        if provider not in _PROVIDER_BASE_URL:
            logger.warning("未知 SEARCH_PROVIDER=%s，回退到 tavily", provider)
            provider = "tavily"
        self.provider: str = provider
        self.search_key: str = search_key
        self.base_url: str = _PROVIDER_BASE_URL[self.provider]

    # ------------------------------------------------------------------ #
    # 响应校验（provider 感知）
    # ------------------------------------------------------------------ #
    def validate_response(self, response: Dict) -> bool:
        """按当前服务商校验响应。"""
        if self.provider == "jina":
            return response.get("code") == 1 or isinstance(response.get("data"), list)
        return "results" in response

    def parse_error(self, response: Dict) -> str:
        """解析错误信息。"""
        if self.provider == "jina":
            return (f"Jina 搜索失败: code={response.get('code')} "
                    f"status={response.get('status')}")
        if "error" in response:
            return str(response["error"])
        return f"搜索失败: {response}"

    # ------------------------------------------------------------------ #
    # 对外主入口
    # ------------------------------------------------------------------ #
    @handle_api_errors
    def search(self, query: str, max_results: int = 10,
               search_type: str = "web", search_depth: str = "advanced",
               timeout: int = 30) -> WebSearchResponse:
        """执行搜索，统一返回 :class:`WebSearchResponse`。

        Args:
            query: 搜索查询。
            max_results: 最大结果数（夹到 [1, 10]）。
            search_type: ``web`` / ``news``（Tavily 映射到 ``topic``；Jina 不区分，
                仅用于结果 ``source_type`` 标记）。
            search_depth: ``basic`` / ``advanced``（仅 Tavily 生效）。
            timeout: HTTP 超时（秒）。
        """
        num = max(1, min(max_results, 10))
        is_news = search_type == "news"

        # _retry_request 提供指数退避重试；最终失败抛 APIError，由上层兜底。
        raw: Dict = self._retry_request(
            self._request_raw, query, num, search_type, search_depth, timeout
        )
        results = self._normalize(raw, is_news)
        return WebSearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            search_time=0.0,
            sources=[self.provider],
        )

    def _request_raw(self, query: str, num: int, search_type: str,
                     search_depth: str, timeout: int) -> Dict:
        """按当前服务商发起实际请求，返回原始 JSON 字典。"""
        if self.provider == "jina":
            return self._request_jina(query, num, timeout)
        return self._request_tavily(query, num, search_type, search_depth, timeout)

    def _request_jina(self, query: str, num: int, timeout: int) -> Dict:
        """``POST https://s.jina.ai/`` body ``{q, num}``，需 ``Accept: application/json``。"""
        headers = {"Accept": "application/json", "X-Retain-Images": "none"}
        if self.search_key:
            headers["Authorization"] = f"Bearer {self.search_key}"
        return self._make_request(
            "POST", "", data={"q": query, "num": num},
            headers=headers, timeout=timeout,
        )

    def _request_tavily(self, query: str, num: int, search_type: str,
                        search_depth: str, timeout: int) -> Dict:
        """``POST /search``，使用 Tavily 合法字段（topic/max_results/search_depth）。"""
        topic = "news" if search_type == "news" else "general"
        data = {
            "query": query,
            "topic": topic,
            "max_results": num,
            "search_depth": search_depth if search_depth in ("basic", "advanced") else "basic",
            "include_raw_content": True,
        }
        headers = self.config.get_headers("search")
        if self.search_key:
            headers["Authorization"] = f"Bearer {self.search_key}"
        return self._make_request(
            "POST", "search", data=data, headers=headers, timeout=timeout,
        )

    # ------------------------------------------------------------------ #
    # 归一化：把任意服务商的原始响应统一成 List[SearchResult]
    # ------------------------------------------------------------------ #
    def _normalize(self, raw: Dict, is_news: bool) -> List[SearchResult]:
        items = raw.get("data") if self.provider == "jina" else raw.get("results")
        if not isinstance(items, list):
            return []

        source_type = SourceType.NEWS if is_news else SourceType.WEB
        results: List[SearchResult] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            url = self._as_str(item.get("url"))
            if not url.startswith(("http://", "https://")):
                # 无有效 URL 的条目直接跳过，绝不因单条异常拖垮整次搜索
                continue
            snippet, full = self._extract_text(item)
            try:
                results.append(SearchResult(
                    title=self._as_str(item.get("title")) or url,
                    url=url,
                    content=snippet,
                    score=item.get("score", 0.0),  # schema validator 负责归一化
                    source=self._hostname(url),
                    source_type=source_type,
                    raw_content=full or None,
                ))
            except Exception as e:  # noqa: BLE001 - 单条失败不影响整体
                logger.debug("解析单条搜索结果失败: %s", e)
                continue
        return results

    def _extract_text(self, item: Dict) -> tuple[str, str]:
        """按服务商提取 (摘要, 全文)。"""
        if self.provider == "jina":
            # Jina: description 是搜索摘要，content 是完整 Markdown 正文
            snippet = self._as_str(item.get("description")) or self._as_str(item.get("content"))
            full = self._as_str(item.get("content"))
            return snippet, full
        # Tavily: content 是摘要，raw_content 是正文
        snippet = self._as_str(item.get("content"))
        full = self._as_str(item.get("raw_content"))
        return snippet, full

    @staticmethod
    def _as_str(v: object) -> str:
        if v is None:
            return ""
        if isinstance(v, str):
            return v
        return str(v)

    @staticmethod
    def _hostname(url: str) -> str:
        try:
            net = urlparse(url).netloc
            return net.lower() or url
        except Exception:  # noqa: BLE001
            return url
