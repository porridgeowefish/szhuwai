"""
Search API Tests
================

Tests for the provider-aware SearchClient (Jina / Tavily).
"""

from unittest.mock import patch

import pytest

from src.api.config import APIConfig
from src.api.search_client import SearchClient
from src.schemas.search import WebSearchResponse


class TestSearchClient:
    """测试搜索 API 客户端"""

    @pytest.fixture(autouse=True)
    def _isolate_search_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """清掉搜索相关 env，使各 provider 行为可预期（不被 .env 的 TAVILY_API_KEY 触发自动降级）。"""
        for key in ("TAVILY_API_KEY", "JINA_API_KEY", "SEARCH_API_KEY"):
            monkeypatch.delenv(key, raising=False)

    def test_client_initialization_default_tavily(self):
        """默认服务商为 tavily，base_url 指向 api.tavily.com"""
        config = APIConfig()
        client = SearchClient(config)

        assert client.provider == "tavily"
        assert client.base_url == "https://api.tavily.com"
        assert client.config == config

    def test_client_initialization_tavily(self):
        """显式指定 tavily 时 base_url 切换"""
        config = APIConfig(SEARCH_PROVIDER="tavily")
        client = SearchClient(config)

        assert client.provider == "tavily"
        assert client.base_url == "https://api.tavily.com"

    def test_unknown_provider_falls_back_to_tavily(self):
        """未知服务商回退到 tavily（默认）"""
        config = APIConfig(SEARCH_PROVIDER="bing")
        client = SearchClient(config)
        assert client.provider == "tavily"

    def test_auto_fallback_to_tavily_when_no_jina_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """选了 jina 但没有有效 Jina key，且环境存在 Tavily key → 自动降级到 tavily"""
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
        client = SearchClient(APIConfig(SEARCH_PROVIDER="jina"))  # 显式 jina，无 jina key
        assert client.provider == "tavily"
        assert client.search_key == "tvly-test-key"

    def test_keeps_jina_when_valid_jina_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """配了有效 Jina key（jina_ 前缀）时不降级"""
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
        client = SearchClient(APIConfig(SEARCH_PROVIDER="jina", SEARCH_API_KEY="jina_abc123"))
        assert client.provider == "jina"
        assert client.search_key == "jina_abc123"

    def test_validate_response_jina(self):
        """Jina 响应校验：code==1 或含 data 列表"""
        config = APIConfig(SEARCH_PROVIDER="jina")
        client = SearchClient(config)

        assert client.validate_response({"code": 1, "status": 20000, "data": []}) is True
        assert client.validate_response({"code": 1, "data": [{"title": "x"}]}) is True
        assert client.validate_response({"code": 4, "status": 40001}) is False
        assert client.validate_response({"random": 1}) is False

    def test_validate_response_tavily(self):
        """Tavily 响应校验：必须含 results"""
        config = APIConfig(SEARCH_PROVIDER="tavily")
        client = SearchClient(config)

        assert client.validate_response({"results": [], "query": "q"}) is True
        assert client.validate_response({"error": "bad"}) is False

    @patch("src.api.search_client.SearchClient._make_request")
    def test_jina_search_normalize(self, mock_request):
        """Jina 返回归一化：source 取 hostname、content 取 description、raw_content 取正文"""
        mock_request.return_value = {
            "code": 1,
            "status": 20000,
            "data": [
                {
                    "title": "徒步攻略",
                    "url": "https://www.cnblogs.com/p/1",
                    "description": "这是摘要",
                    "content": "完整的 Markdown 正文",
                }
            ],
        }

        client = SearchClient(APIConfig(SEARCH_PROVIDER="jina"))
        resp = client.search("徒步攻略", max_results=5)

        assert isinstance(resp, WebSearchResponse)
        assert resp.sources == ["jina"]
        assert len(resp.results) == 1
        r = resp.results[0]
        assert r.url == "https://www.cnblogs.com/p/1"
        assert r.source == "www.cnblogs.com"          # 由 hostname 派生
        assert r.content == "这是摘要"                  # description → content
        assert r.raw_content == "完整的 Markdown 正文"   # content → raw_content
        assert r.score == 0.0                           # Jina 无分数 → 0.0，不崩

    @patch("src.api.search_client.SearchClient._make_request")
    def test_jina_search_skips_invalid_url(self, mock_request):
        """无有效 URL 的条目被跳过，不抛异常"""
        mock_request.return_value = {
            "code": 1,
            "data": [
                {"title": "无URL", "url": "", "content": "x"},
                {"title": "坏URL", "url": "not-a-url", "content": "y"},
                {"title": "好", "url": "https://example.com/a", "description": "d"},
            ],
        }
        client = SearchClient(APIConfig(SEARCH_PROVIDER="jina"))
        resp = client.search("q")

        assert len(resp.results) == 1
        assert resp.results[0].url == "https://example.com/a"

    @patch("src.api.search_client.SearchClient._make_request")
    def test_tavily_uses_correct_params(self, mock_request):
        """Tavily 只发合法字段（topic/max_results/search_depth），不含 search_type"""
        mock_request.return_value = {"results": []}

        client = SearchClient(APIConfig(SEARCH_PROVIDER="tavily"))
        client.search("深圳天气", max_results=5, search_depth="advanced")

        assert mock_request.called
        _args, kwargs = mock_request.call_args
        data = kwargs["data"]
        assert data["query"] == "深圳天气"
        assert data["topic"] == "general"
        assert data["max_results"] == 5
        assert data["search_depth"] == "advanced"
        assert "search_type" not in data          # 非法字段已移除
        assert "timeout" not in data              # timeout 是 HTTP 层，不是 body

    def test_score_clamp_handles_out_of_range(self):
        """score 越界/非数不会触发校验崩溃"""
        from src.schemas.search import SearchResult

        r = SearchResult(title="t", url="https://x.com", content="c",
                         score=1.7, source="x.com")
        assert r.score == 1.0
        r2 = SearchResult(title="t", url="https://x.com", content="c",
                          score="not-a-number", source="x.com")
        assert r2.score == 0.0
