"""
搜索服务
========

封装网络搜索逻辑。
"""

from typing import List

from loguru import logger

from src.schemas.search import WebSearchResponse
from src.api.search_client import SearchClient


class SearchService:
    """搜索服务"""

    def __init__(self):
        """初始化服务"""
        self.client = SearchClient()

    def search(
        self,
        keywords: str,
        search_types: List[str] = None,
        max_results: int = 5
    ) -> List[WebSearchResponse]:
        """
        执行多维度搜索

        Args:
            keywords: 搜索关键词
            search_types: 搜索类型列表，默认为 ['景点', '救援', '攻略', '装备']
            max_results: 每组搜索的最大结果数

        Returns:
            List[WebSearchResponse]: 搜索结果列表
        """
        if search_types is None:
            search_types = ['景点', '救援', '攻略', '装备']

        # 构建搜索查询
        search_queries = self._build_search_queries(keywords, search_types)
        logger.info(f"搜索关键词: {keywords}, 类型: {search_types}")

        all_results = []
        for query in search_queries:
            try:
                logger.info(f"执行搜索查询: {query}")
                result = self.client.search(query, max_results=max_results)
                if result and isinstance(result, WebSearchResponse):
                    all_results.append(result)
            except Exception as e:
                logger.error(f"搜索失败 [{query}]: {e}")
                continue

        return all_results

    def _build_search_queries(self, keywords: str, search_types: List[str]) -> List[str]:
        """构建搜索查询列表"""
        queries = []

        if '景点' in search_types:
            queries.append(f"{keywords} 景点 景区 旅游")

        if '救援' in search_types:
            queries.append(f"{keywords} 户外徒步 应急救援队 报警电话")

        if '攻略' in search_types:
            queries.append(f"{keywords} 徒步攻略 登山路线 注意事项")

        if '装备' in search_types:
            queries.append(f"{keywords} 徒步装备 登山装备 露营装备推荐")

        return queries
