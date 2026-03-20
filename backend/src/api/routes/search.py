"""
搜索查询路由
============

POST /api/v1/search/query - 搜索查询
"""

from typing import List, Optional

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel, Field

from src.schemas.search import WebSearchResponse
from src.api.search_client import SearchClient

router = APIRouter(prefix="/search", tags=["搜索查询"])


class SearchQueryResponse(BaseModel):
    """搜索查询响应"""
    success: bool = Field(True, description="请求是否成功")
    data: List[WebSearchResponse] = Field(default_factory=list, description="搜索结果")
    message: Optional[str] = Field(None, description="附加消息")


@router.post("/query", response_model=SearchQueryResponse)
async def query_search(
    keywords: str = Form(..., description="搜索关键词"),
    max_results: int = Form(5, description="每组搜索的最大结果数")
) -> SearchQueryResponse:
    """
    执行搜索查询

    - **keywords**: 搜索关键词（多个用空格分隔）
    - **max_results**: 每组搜索的最大结果数
    """
    try:
        client = SearchClient()

        # 构建搜索查询
        search_queries = [
            f"{keywords} 景点 景区 旅游",
            f"{keywords} 户外徒步 应急救援队 报警电话",
            f"{keywords} 徒步攻略 登山路线 注意事项",
            f"{keywords} 徒步装备 登山装备 露营装备推荐"
        ]

        all_results = []
        for query in search_queries:
            try:
                result = client.search(query, max_results=max_results)
                if result and isinstance(result, WebSearchResponse):
                    all_results.append(result)
            except Exception:
                continue

        return SearchQueryResponse(
            success=True,
            data=all_results,
            message=f"搜索完成，共 {len(all_results)} 组结果"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索查询失败: {str(e)}"
        )
