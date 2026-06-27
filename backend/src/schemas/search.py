"""
Web Search API Schemas
====================

Schema definitions for web search results and queries.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Any

from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    """搜索来源类型"""
    WEB = "web"
    NEWS = "news"
    ACADEMIC = "academic"
    FORUM = "forum"


class SearchResult(BaseModel):
    """搜索结果"""
    title: str = Field(..., description="标题")
    url: str = Field(..., description="URL")
    content: str = Field(..., description="内容摘要")
    score: float = Field(default=0.0, description="相关度评分（归一化到 [0,1]，缺失/异常记 0.0）")
    source: str = Field(..., description="来源网站")
    source_type: SourceType = Field(default=SourceType.WEB, description="来源类型")
    published_date: Optional[datetime] = Field(None, description="发布日期")
    relevance_tags: List[str] = Field(default_factory=list, description="相关标签")
    raw_content: Optional[str] = Field(None, description="原始内容（高级搜索时返回）")
    favicon: Optional[str] = Field(None, description="网站图标URL")

    @field_validator('score', mode='before')
    @classmethod
    def normalize_score(cls, v: Any) -> float:
        """相关度评分归一化：非数/缺失→0.0，越界→夹到 [0,1]。

        不同搜索服务商返回的评分口径不一（Jina/SerpAPI 不返回分数，
        Tavily 返回 [0,1]），统一归一化避免 Pydantic 校验崩溃。
        """
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.0
        if f < 0.0:
            return 0.0
        if f > 1.0:
            return 1.0
        return f

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """简单的URL验证"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL必须以http://或https://开头')
        return v

    @field_validator('content')
    @classmethod
    def clean_content(cls, v: str) -> str:
        """清理内容"""
        if v:
            # 移除多余的空白字符
            v = ' '.join(v.split())
            # 限制长度
            if len(v) > 1000:
                v = v[:1000] + '...'
        return v

    @property
    def is_trusted_source(self) -> bool:
        """是否为可信来源"""
        trusted_domains = [
            'gov.cn', 'edu.cn', 'org', 'gov', 'edu',
            'weather.com', 'gaode.com', 'map.qq.com'
        ]
        return any(domain in self.source for domain in trusted_domains)

    @property
    def content_preview(self) -> str:
        """内容预览（前100字符）"""
        if self.content:
            return self.content[:100] + ('...' if len(self.content) > 100 else '')
        return ''


class WebSearchResponse(BaseModel):
    """搜索响应"""
    query: str = Field(..., description="搜索查询")
    results: List[SearchResult] = Field(default_factory=list, description="搜索结果")
    total_results: int = Field(default=0, ge=0, description="总结果数")
    search_time: float = Field(default=0.0, ge=0, description="搜索耗时（秒）")
    sources: List[str] = Field(default_factory=list, description="搜索来源")

    @field_validator('total_results')
    @classmethod
    def validate_total_results(cls, v: int, info: Any) -> int:
        """确保总结果数与实际结果数一致"""
        if info.data.get('results'):
            actual_count = len(info.data['results'])
            if v != actual_count:
                # 如果不一致，使用实际数量
                return actual_count
        return v

    @property
    def avg_score(self) -> float:
        """平均相关度评分"""
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)

    @property
    def trusted_results_count(self) -> int:
        """可信结果数量"""
        return sum(1 for r in self.results if r.is_trusted_source)

    def get_results_by_type(self, source_type: SourceType) -> List[SearchResult]:
        """按类型获取搜索结果"""
        return [r for r in self.results if r.source_type == source_type]

    def get_top_results(self, n: int = 5) -> List[SearchResult]:
        """获取前N个最高评分的结果"""
        return sorted(self.results, key=lambda x: x.score, reverse=True)[:n]

    def has_recent_results(self, days: int = 30) -> bool:
        """检查是否有最近的结果"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return any(r.published_date and r.published_date > cutoff_date
                  for r in self.results)


class SearchEmergencyContact(BaseModel):
    """从搜索结果中提取的应急电话候选。"""
    name: str = Field(..., description="机构或电话名称")
    phone: str = Field(..., description="电话号码")
    contact_type: str = Field(default="救援", description="电话类型")


class WebSearchInsight(BaseModel):
    """搜索结果经 AI 或本地规则提炼后的可展示结论。"""
    summary: str = Field(default="", description="沿途风光、攻略和应急信息摘要")
    emergency_contacts: List[SearchEmergencyContact] = Field(default_factory=list)
