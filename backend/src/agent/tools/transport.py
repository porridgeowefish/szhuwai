"""
交通路线工具
============

提供交通路线规划功能。
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.services.transport_service import TransportService


class TransportRouteInput(BaseModel):
    """交通路线输入参数"""
    departure_point: str = Field(
        ...,
        description="出发地点（文字地址），例如：北京市朝阳区国贸"
    )
    destination_coord: str = Field(
        ...,
        description="目的地坐标（格式：经度,纬度），例如：116.407526,39.904030"
    )


@tool("transport_route", args_schema=TransportRouteInput)
def transport_route(departure_point: str, destination_coord: str) -> str:
    """
    规划从出发地点到目的地的交通路线。

    该工具会提供多种交通方式的路线规划，包括：
    - 驾车路线（距离、时间、过路费）
    - 公交/地铁路线（换乘方案、费用、时间）
    - 推荐方案（根据距离和可用性）
    - 最快和最便宜方案对比

    Args:
        departure_point: 出发地点（文字地址）
        destination_coord: 目的地坐标（"lon,lat" 格式）

    Returns:
        str: 格式化的交通路线信息字符串
    """
    try:
        # 创建服务实例
        service = TransportService()

        # 规划路线
        routes = service.plan(departure_point, destination_coord)

        # 格式化输出
        output_parts = [
            "=== 交通路线规划 ===",
            f"起点: {routes.origin.address}",
            f"终点: {routes.destination.address}",
            f"",
            "=== 路线汇总 ==="
        ]

        # 添加汇总信息
        if routes.summary.total_distance:
            output_parts.append(f"总距离: {routes.summary.total_distance}")
        if routes.summary.total_time:
            output_parts.append(f"总时间: {routes.summary.total_time}")
        if routes.summary.cost:
            output_parts.append(f"费用: {routes.summary.cost}")
        if routes.fastest_mode:
            output_parts.append(f"最快方式: {routes.fastest_mode}")
        if routes.cheapest_mode:
            output_parts.append(f"最便宜方式: {routes.cheapest_mode}")
        if routes.recommended_mode:
            output_parts.append(f"推荐方案: {routes.recommended_mode}")

        output_parts.append("")

        # 添加驾车路线
        if routes.outbound and "driving" in routes.outbound:
            driving = routes.outbound["driving"]
            output_parts.extend([
                "=== 驾车路线 ===",
                f"可用: {'是' if driving.get('available', False) else '否'}",
                f"距离: {driving.get('distance_km', 0):.1f} 公里",
                f"时间: {driving.get('duration_min', 0)} 分钟",
                f"过路费: {driving.get('tolls_yuan', 0)} 元",
                f""
            ])

        # 添加公交路线
        if routes.outbound and "transit" in routes.outbound:
            transit = routes.outbound["transit"]
            output_parts.extend([
                "=== 公交/地铁路线 ===",
                f"可用: {'是' if transit.get('available', False) else '否'}",
                f"距离: {transit.get('distance_km', 0):.1f} 公里",
                f"时间: {transit.get('duration_min', 0)} 分钟",
                f"费用: {transit.get('cost_yuan', 0)} 元",
                f"步行距离: {transit.get('walking_distance', 0)} 米"
            ])

            # 添加公交段详细信息
            segments = transit.get('segments')
            if segments:
                output_parts.append("")
                output_parts.append("公交段详情:")
                for i, seg in enumerate(segments, 1):
                    seg_type = seg.get('type', 'unknown')
                    line_name = seg.get('line_name', '未知')
                    dep_stop = seg.get('departure_stop', '')
                    arr_stop = seg.get('arrival_stop', '')
                    duration = seg.get('duration_min', 0)
                    output_parts.append(
                        f"  {i}. [{seg_type}] {line_name}: {dep_stop} -> {arr_stop} "
                        f"({duration}分钟)"
                    )

            output_parts.append("")

        # 添加多条公交路线方案
        if routes.transit_routes and len(routes.transit_routes) > 1:
            output_parts.append("=== 其他公交方案 ===")
            for i, route in enumerate(routes.transit_routes[1:], 1):  # 跳过第一条
                line_name = route.line_name or "未知线路"
                output_parts.extend([
                    f"方案 {i}: {line_name}",
                    f"  时间: {route.duration_min} 分钟, "
                    f"费用: {route.cost_yuan} 元, "
                    f"步行: {route.walking_distance} 米",
                    f""
                ])

        # 添加打车费用
        if routes.taxi_cost_yuan:
            output_parts.append(f"打车费用预估: {routes.taxi_cost_yuan} 元")

        return "\n".join(output_parts)

    except Exception as e:
        return f"错误: 交通路线规划失败 - {str(e)}"
