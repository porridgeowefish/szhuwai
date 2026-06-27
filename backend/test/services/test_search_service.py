"""
SearchService Tests
===================

测试搜索服务的查询构造、术语清洗与摘要降级（不触网、不依赖 LLM key）。
"""

from src.api.config import APIConfig
from src.services.search_service import SearchService


class TestSearchService:
    """测试 SearchService 的非网络逻辑"""

    def test_build_search_queries_excludes_bilibili(self) -> None:
        """B 站已从搜索平台过滤词中移除，其余平台保留"""
        queries = SearchService(APIConfig())._build_search_queries("武功山", ["景点", "攻略"])
        joined = " ".join(queries)

        assert "bilibili.com" not in joined
        assert "douyin.com" in joined
        assert "xiaohongshu.com" in joined
        assert all("武功山" in q for q in queries)

    def test_clean_term_replaces_poi_jargon(self) -> None:
        """高德线索里的 POI / 逆地理 等术语被清洗为口语"""
        assert SearchService._clean_term("附近POI：加油站") == "附近有 加油站"
        assert SearchService._clean_term("逆地理归属") == "属地归属"
        assert SearchService._clean_term("") == ""

    def test_synthesize_insight_falls_back_and_cleans_terms(self) -> None:
        """无 LLM key 时走本地降级摘要，且 local_context 里的 POI 术语被清洗掉"""
        svc = SearchService(APIConfig())  # LLM_API_KEY 默认空 → 直接走 fallback，不触网
        insight = svc.synthesize_insight("武功山", [], ["附近POI：金顶"])

        assert "POI" not in insight.summary
        assert "金顶" in insight.summary
