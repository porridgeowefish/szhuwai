"""
Search API Tests
================

Tests for the SearchClient (Tavily) integration.
"""

import pytest
from unittest.mock import MagicMock, patch
from api.config import APIConfig
from api.search_client import SearchClient
from schemas.search import SearchResult, WebSearchResponse


class TestSearchClient:
    """测试搜索 API 客户端"""

    def test_client_initialization(self):
        """测试搜索客户端初始化"""
        config = APIConfig()
        client = SearchClient(config)

        assert client.base_url == config.SEARCH_BASE_URL
        assert client.config == config
        assert client.search_history == []

    def test_validate_response_format(self):
        """测试搜索响应格式验证"""
        config = APIConfig()
        client = SearchClient(config)

        valid_response = {
            "results": [],
            "query": "test",
            "total_results": 0
        }
        assert client.validate_response(valid_response) is True

        invalid_response = {"data": "test"}
        assert client.validate_response(invalid_response) is False

    def test_search_history_tracking(self):
        """测试搜索历史记录"""
        config = APIConfig()
        client = SearchClient(config)

        client.search_history.append({
            "query": "test1",
            "max_results": 10
        })
        client.search_history.append({
            "query": "test2",
            "max_results": 5
        })

        history = client.get_search_history(limit=10)
        assert len(history) == 2

    def test_search_history_clear(self):
        """测试清空搜索历史"""
        config = APIConfig()
        client = SearchClient(config)

        client.search_history.append({"query": "test", "max_results": 10})
        assert len(client.search_history) == 1

        client.clear_search_history()
        assert len(client.search_history) == 0

    def test_url_validation(self):
        """测试 URL 验证"""
        config = APIConfig()
        client = SearchClient(config)

        # Mock requests.head
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            assert client.validate_url("https://example.com") is True

        # Test with exception
        with patch('requests.head', side_effect=Exception):
            assert client.validate_url("https://nonexistent-domain-12345.com") is False
