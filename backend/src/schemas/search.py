"""
Web Search API Schemas
====================

Schema definitions for web search results and queries.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any

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
    score: float = Field(..., ge=0, le=1, description="相关度评分")
    source: str = Field(..., description="来源网站")
    source_type: SourceType = Field(default=SourceType.WEB, description="来源类型")
    published_date: Optional[datetime] = Field(None, description="发布日期")
    relevance_tags: List[str] = Field(default_factory=list, description="相关标签")
    raw_content: Optional[str] = Field(None, description="原始内容（高级搜索时返回）")
    favicon: Optional[str] = Field(None, description="网站图标URL")

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


def optimize_search_query(original_query: str, context: Dict[str, Any]) -> str:
    """优化搜索查询"""
    # 1. 提取关键信息
    locations = context.get('locations', [])
    dates = context.get('dates', [])
    activities = context.get('activities', [])

    # 2. 构建增强查询
    enhanced = original_query

    # 添加地理位置
    if locations:
        enhanced += f" {' '.join(locations)}"

    # 添加时间信息
    if dates:
        enhanced += f" {' '.join(dates)}"

    # 添加活动类型
    if activities:
        enhanced += " 徒步 登山 户外"

    # 3. 使用布尔运算符
    enhanced = enhanced.replace('和', ' OR ')

    return enhanced


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """从文本中提取关键词"""
    # 简单的关键词提取
    import re
    # 移除停用词
    stop_words = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'
    }

    # 提取中文词语
    words = re.findall(r'[\u4e00-\u9fff]+', text)

    # 过滤停用词并统计词频
    word_count: Dict[str, int] = {}
    for word in words:
        if len(word) >= 2 and word not in stop_words:
            word_count[word] = word_count.get(word, 0) + 1

    # 按词频排序
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)

    # 返回前N个关键词
    return [word for word, count in sorted_words[:max_keywords]]