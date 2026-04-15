"""
轨迹分析工具
============

提供 GPX/KML 轨迹文件解析和分析功能。
"""

from pathlib import Path
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.services.track_service import TrackService


class TrackAnalyzeInput(BaseModel):
    """轨迹分析输入参数"""
    file_path: str = Field(
        ...,
        description="GPX 或 KML 轨迹文件的绝对路径，例如：/path/to/track.gpx"
    )


@tool("track_analyze", args_schema=TrackAnalyzeInput)
def track_analyze(file_path: str) -> str:
    """
    分析 GPX/KML 轨迹文件，提取距离、爬升、难度、坐标等信息。

    该工具会解析轨迹文件并返回详细的轨迹分析结果，包括：
    - 总里程（公里）
    - 总爬升/下降（米）
    - 难度等级和评分
    - 起终点坐标
    - 预计用时

    Args:
        file_path: GPX/KML 轨迹文件路径

    Returns:
        str: 格式化的轨迹分析结果字符串
    """
    try:
        # 创建服务实例
        service = TrackService()

        # 解析轨迹文件
        result = service.analyze(file_path)

        # 坐标纠偏
        key_points = service.correct_coordinates(result)

        # 格式化输出
        output_parts = [
            "=== 轨迹分析结果 ===",
            f"轨迹名称: {result.track_name or '未知'}",
            f"总里程: {result.total_distance_km:.2f} 公里",
            f"总爬升: {result.total_ascent_m:.0f} 米",
            f"总下降: {result.total_descent_m:.0f} 米",
            f"最高海拔: {result.max_elevation_m:.0f} 米",
            f"最低海拔: {result.min_elevation_m:.0f} 米",
            f"平均海拔: {result.avg_elevation_m:.0f} 米",
            f"",
            f"难度等级: {result.difficulty_level}",
            f"难度评分: {result.difficulty_score:.0f}/100",
            f"预计用时: {result.estimated_duration_hours:.1f} 小时",
            f"安全风险: {result.safety_risk}",
            f"",
            "=== 关键坐标点 (GCJ02) ==="
        ]

        # 添加关键点坐标
        if 'start' in key_points:
            pt = key_points['start']
            output_parts.append(f"起点: ({pt.lon:.6f}, {pt.lat:.6f}), 海拔 {pt.elevation:.0f}m")

        if 'end' in key_points:
            pt = key_points['end']
            output_parts.append(f"终点: ({pt.lon:.6f}, {pt.lat:.6f}), 海拔 {pt.elevation:.0f}m")

        if 'highest' in key_points:
            pt = key_points['highest']
            output_parts.append(f"最高点: ({pt.lon:.6f}, {pt.lat:.6f}), 海拔 {pt.elevation:.0f}m")

        # 添加地形分析
        if result.terrain_analysis:
            output_parts.append("")
            output_parts.append("=== 地形变化路段 ===")
            for i, segment in enumerate(result.terrain_analysis, 1):
                change_type = "大爬升" if segment.change_type == "large_ascent" else "大下降"
                output_parts.append(
                    f"路段 {i}: {change_type} {segment.elevation_diff:.0f}米, "
                    f"坡度 {segment.gradient_percent:.1f}%, "
                    f"距离 {segment.distance_m:.0f}米"
                )

        return "\n".join(output_parts)

    except FileNotFoundError as e:
        return f"错误: 文件不存在 - {str(e)}"
    except ValueError as e:
        return f"错误: 解析失败 - {str(e)}"
    except Exception as e:
        return f"错误: 轨迹分析失败 - {str(e)}"
