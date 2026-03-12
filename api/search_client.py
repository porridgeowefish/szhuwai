"""
Search API Client
=================

Client for integrating with Tavily Search API.
"""

import logging
from typing import Dict, Optional, List
import json

logger = logging.getLogger(__name__)

from . import BaseAPIClient, handle_api_errors, APIError
from .config import api_config
from schemas.search import SearchResult, WebSearchResponse


class SearchClient(BaseAPIClient):
    """搜索API客户端"""

    def __init__(self, config=None):
        super().__init__(config or api_config)
        self.base_url = self.config.SEARCH_BASE_URL
        self.search_history = []

    def validate_response(self, response: Dict) -> bool:
        """验证API响应格式"""
        return "results" in response and "query" in response

    def parse_error(self, response: Dict) -> str:
        """解析错误信息"""
        if "error" in response:
            return response["error"]
        return f"搜索失败: {response}"

    @handle_api_errors
    def search(self, query: str, max_results: int = 10,
                search_type: str = "web", timeout: int = 30) -> WebSearchResponse:
        """执行搜索"""
        endpoint = "/search"
        params = {
            "query": query,
            "max_results": max_results,
            "timeout": timeout,
            "search_type": search_type
        }

        # 添加搜索历史
        self.search_history.append({
            "query": query,
            "timestamp": params.get("timestamp", ""),
            "max_results": max_results
        })

        response = self._make_request("POST", endpoint, data=params)

        # 转换结果
        results = []
        for result_data in response.get("results", []):
            result = SearchResult(
                title=result_data.get("title", ""),
                url=result_data.get("url", ""),
                content=result_data.get("content", ""),
                score=result_data.get("score", 0.0),
                source=result_data.get("source", ""),
                source_type=result_data.get("source_type", "web"),
                published_date=result_data.get("published_date"),
                relevance_tags=result_data.get("relevance_tags", [])
            )
            results.append(result)

        return WebSearchResponse(
            query=query,
            results=results,
            total_results=response.get("total_results", len(results)),
            search_time=response.get("search_time", 0.0),
            sources=response.get("sources", [])
        )

    @handle_api_errors
    def search_with_context(self, original_query: str, context: Dict,
                           max_results: int = 10) -> WebSearchResponse:
        """根据上下文优化搜索"""
        # 优化搜索查询
        from ..schemas.search import optimize_search_query
        enhanced_query = optimize_search_query(original_query, context)

        # 执行搜索
        return self.search(enhanced_query, max_results)

    @handle_api_errors
    def news_search(self, query: str, max_results: int = 10,
                    from_date: str = None, to_date: str = None) -> WebSearchResponse:
        """新闻搜索"""
        endpoint = "/search/news"
        params = {
            "query": query,
            "max_results": max_results,
            "from_date": from_date,
            "to_date": to_date
        }

        response = self._make_request("POST", endpoint, data=params)

        # 转换结果
        results = []
        for result_data in response.get("results", []):
            result = SearchResult(
                title=result_data.get("title", ""),
                url=result_data.get("url", ""),
                content=result_data.get("content", ""),
                score=result_data.get("score", 0.0),
                source=result_data.get("source", ""),
                source_type="news",
                published_date=result_data.get("published_date"),
                relevance_tags=result_data.get("relevance_tags", [])
            )
            results.append(result)

        return WebSearchResponse(
            query=query,
            results=results,
            total_results=response.get("total_results", len(results)),
            search_time=response.get("search_time", 0.0),
            sources=["tavily"]
        )

    @handle_api_errors
    def academic_search(self, query: str, max_results: int = 10,
                       year_start: int = None, year_end: int = None) -> WebSearchResponse:
        """学术搜索"""
        endpoint = "/search/academic"
        params = {
            "query": query,
            "max_results": max_results,
            "year_start": year_start,
            "year_end": year_end
        }

        response = self._make_request("POST", endpoint, data=params)

        # 转换结果
        results = []
        for result_data in response.get("results", []):
            result = SearchResult(
                title=result_data.get("title", ""),
                url=result_data.get("url", ""),
                content=result_data.get("content", ""),
                score=result_data.get("score", 0.0),
                source=result_data.get("source", ""),
                source_type="academic",
                published_date=result_data.get("published_date"),
                relevance_tags=result_data.get("relevance_tags", [])
            )
            results.append(result)

        return WebSearchResponse(
            query=query,
            results=results,
            total_results=response.get("total_results", len(results)),
            search_time=response.get("search_time", 0.0),
            sources=["academic_api"]
        )

    def get_search_history(self, limit: int = 10) -> List[Dict]:
        """获取搜索历史"""
        return self.search_history[-limit:]

    def clear_search_history(self):
        """清空搜索历史"""
        self.search_history = []

    def analyze_trending_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """分析热门关键词"""
        from ..schemas.search import extract_keywords
        return extract_keywords(text, max_keywords)

    def get_similar_queries(self, query: str, max_similar: int = 5) -> List[str]:
        """获取相似查询"""
        # 基于查询关键词生成相似查询
        keywords = self.analyze_trending_keywords(query, 5)
        similar_queries = []

        for keyword in keywords:
            # 生成变体查询
            variants = [
                f"{keyword} 户外活动",
                f"{keyword} 徒步路线",
                f"{keyword} 攻略",
                f"{keyword} 注意事项"
            ]
            similar_queries.extend(variants)

        # 去重并限制数量
        similar_queries = list(set(similar_queries))[:max_similar]
        return similar_queries

    def validate_url(self, url: str) -> bool:
        """验证URL有效性"""
        try:
            import requests
            response = requests.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False

    def crawl_page(self, url: str, max_length: int = 2000) -> Optional[str]:
        """爬取页面内容摘要"""
        try:
            import requests
            from bs4 import BeautifulSoup

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # 使用BeautifulSoup解析
            soup = BeautifulSoup(response.content, 'html.parser')

            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()

            # 获取文本内容
            text = soup.get_text()

            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # 限制长度
            if len(text) > max_length:
                text = text[:max_length] + "..."

            return text

        except Exception as e:
            logger.error(f"爬取页面失败 {url}: {str(e)}")
            return None

    def search_emergency_contacts(self, location: str) -> List[Dict]:
        """搜索应急救援电话（使用百度和抖音）"""
        emergency_contacts = []

        # 构建搜索查询
        queries = [
            f"{location} 户外 应急救援电话 报警",
            f"{location} 蓝天救援队电话",
            f"{location} 景区报警电话",
            f"{location} 户外运动应急救援",
            f"{location} 旅游局紧急电话"
        ]

        # 使用百度和抖音作为搜索引擎
        search_domains = [
            "www.baidu.com",
            "www.douyin.com"
        ]

        for query in queries:
            # 搜索结果中提取电话号码
            try:
                response = self.search(query, max_results=5)

                for result in response.results:
                    # 从内容中提取电话号码
                    import re
                    phone_pattern = r'(1[3-9]\d{9}|0\d{2,3}-?\d{7,8})'
                    phones = re.findall(phone_pattern, result.content)

                    for phone in phones:
                        # 去重
                        if not any(ec['phone'] == phone for ec in emergency_contacts):
                            emergency_contacts.append({
                                'name': result.title.split(' - ')[0] if ' - ' in result.title else result.title,
                                'phone': phone,
                                'type': '救援',
                                'source': result.source,
                                'url': result.url
                            })

            except Exception as e:
                logger.error(f"搜索应急救援电话失败: {query}, 错误: {str(e)}")
                continue

        # 去重并排序
        emergency_contacts = list({ec['phone']: ec for ec in emergency_contacts}).values()

        # 添加一些常见救援电话作为备选
        common_contacts = [
            {'name': '急救中心', 'phone': '120', 'type': '医疗', 'source': 'system'},
            {'name': '报警电话', 'phone': '110', 'type': '报警', 'source': 'system'},
            {'name': '火警电话', 'phone': '119', 'type': '救援', 'source': 'system'}
        ]

        # 合并并去重
        all_contacts = emergency_contacts + common_contacts
        all_contacts = list({ec['phone']: ec for ec in all_contacts}).values()

        return list(all_contacts)