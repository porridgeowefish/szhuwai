"""
SearchService Tests
===================

测试搜索服务的查询构造、术语清洗与摘要降级（不触网、不依赖 LLM key）。
"""

from src.api.config import APIConfig
from src.schemas.output import WebReference
from src.schemas.search import SearchResult, WebSearchResponse
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

    def test_filter_response_keeps_only_route_matched_results(self) -> None:
        """搜索 API 返回后先按线路名过滤，避免错把其它线路交给 AI 概括。"""
        response = WebSearchResponse(
            query="梧桐山夜爬 徒步攻略",
            results=[
                SearchResult(
                    title="梅沙尖云海攻略",
                    url="https://example.com/meishajian",
                    content="梅沙尖云海和日出路线",
                    source="example.com",
                ),
                SearchResult(
                    title="梧桐山夜爬注意事项",
                    url="https://example.com/wutong",
                    content="梧桐山夜爬全程约 10km，注意头灯和下撤时间。",
                    source="example.com",
                ),
            ],
        )

        filtered = SearchService._filter_response_by_route("梧桐山夜爬", response)

        assert len(filtered.results) == 1
        assert filtered.results[0].title == "梧桐山夜爬注意事项"
        assert "梅沙尖" not in filtered.results[0].content

    def test_clean_web_text_removes_platform_noise_for_llm(self) -> None:
        """LLM 材料前清掉 @/#/英文/emoji/繁体与平台推荐区噪音。"""
        dirty = (
            "7🈷️20正穿黄连盂！！！#神奇的大自然 #黄连盂 9@NaNa "
            "福建龙岩黄连盂，海拔1818，全程10km 耗时6.5小时。"
            "Please login before leaving comments ## 热门分类 法律人物时尚杂志 "
            "balanced.leona 徒步黃連盂｜高山草甸，美到失語 high-quality-icon "
            "原声大片龙岩黄连盂最危险最难的一段。"
        )

        cleaned = SearchService._clean_web_text(dirty)

        assert "@" not in cleaned
        assert "#" not in cleaned
        assert "NaNa" not in cleaned
        assert "Please" not in cleaned
        assert "熱門" not in cleaned
        assert "黃連盂" not in cleaned
        assert "high-quality-icon" not in cleaned
        assert "原声" not in cleaned
        assert "黄连盂" in cleaned
        assert "全程10 耗时6.5小时" in cleaned

    def test_synthesize_from_references_filters_unmatched_and_noisy_fallback(self) -> None:
        """异步 AI 概括入口也要过滤错配引用；无 LLM key 时降级文本同样去噪。"""
        svc = SearchService(APIConfig())
        insight = svc.synthesize_from_references(
            "黄连盂",
            [
                WebReference(
                    title="梅沙尖云海",
                    url="https://example.com/a",
                    snippet="梅沙尖云海攻略",
                    source="example.com",
                ),
                WebReference(
                    title="黄连盂攻略 #徒步 @作者",
                    url="https://example.com/b",
                    snippet="黄连盂草甸路线，全程10km。Please login before leaving comments",
                    source="example.com",
                ),
            ],
        )

        assert "梅沙尖" not in insight.summary
        assert "Please" not in insight.summary
        assert "@" not in insight.summary
        assert "#" not in insight.summary
        assert "黄连盂草甸路线" in insight.summary
