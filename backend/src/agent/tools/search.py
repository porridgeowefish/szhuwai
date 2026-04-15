"""
网络搜索工具
============

提供多维度网络搜索功能。
"""

from typing import List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.services.search_service import SearchService


class WebSearchInput(BaseModel):
    """网络搜索输入参数"""
    keywords: str = Field(
        ...,
        description="搜索关键词，例如：香山 徒步"
    )
    search_types: Optional[List[str]] = Field(
        default=None,
        description="搜索类型列表，可选：['景点', '救援', '攻略', '装备']。默认全部搜索"
    )


@tool("web_search", args_schema=WebSearchInput)
def web_search(keywords: str, search_types: Optional[List[str]] = None) -> str:
    """
    执行多维度网络搜索，获取相关信息。

    该工具会根据关键词进行多个维度的搜索：
    - 景点：景区、景点信息
    - 救援：户外救援队、应急联系方式
    - 攻略：徒步攻略、登山路线、注意事项
    - 装备：徒步装备、登山装备推荐

    Args:
        keywords: 搜索关键词
        search_types: 搜索类型列表（可选）

    Returns:
        str: 格式化的搜索结果字符串
    """
    try:
        # 创建服务实例
        service = SearchService()

        # 执行搜索
        results = service.search(keywords, search_types, max_results=5)

        # 格式化输出
        output_parts = [
            "=== 网络搜索结果 ===",
            f"关键词: {keywords}",
            f"搜索类型: {', '.join(search_types) if search_types else '全部'}",
            f"结果组数: {len(results)}",
            f""
        ]

        if not results:
            output_parts.append("未找到相关搜索结果。")
            return "\n".join(output_parts)

        # 遍历每组搜索结果
        for i, result_group in enumerate(results, 1):
            output_parts.extend([
                f"=== 搜索组 {i} ===",
                f"查询: {result_group.query}",
                f"结果数: {result_group.total_results}",
                f"平均相关度: {result_group.avg_score:.2f}",
                f""
            ])

            # 显示前5个结果
            top_results = result_group.get_top_results(5)
            for j, result in enumerate(top_results, 1):
                output_parts.extend([
                    f"结果 {j}:",
                    f"  标题: {result.title}",
                    f"  URL: {result.url}",
                    f"  来源: {result.source}",
                    f"  相关度: {result.score:.2f}",
                    f"  摘要: {result.content_preview}",
                    f""
                ])

            # 显示可信来源数量
            trusted_count = result_group.trusted_results_count
            if trusted_count > 0:
                output_parts.append(f"✓ 可信来源数量: {trusted_count}")
            output_parts.append("")

        return "\n".join(output_parts)

    except Exception as e:
        return f"错误: 网络搜索失败 - {str(e)}"
