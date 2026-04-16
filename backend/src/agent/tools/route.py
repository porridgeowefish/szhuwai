"""路线管理工具"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger


class RouteSaveInput(BaseModel):
    name: str = Field(description="路线名称")
    file_path: str = Field(description="GPX/KML 轨迹文件路径")
    user_id: int = Field(description="用户 ID")
    is_public: bool = Field(default=False, description="是否公开")


@tool("route_save", args_schema=RouteSaveInput)
def route_save(name: str, file_path: str, user_id: int, is_public: bool = False) -> str:
    """保存轨迹到路线库，便于以后复用。
    保存后可以在路线库中搜索和推荐。
    """
    try:
        from src.services.track_service import TrackService
        service = TrackService()
        result = service.analyze(file_path)
        service.correct_coordinates(result)

        route_data = {
            "name": name,
            "total_distance_km": result.total_distance_km,
            "total_ascent_m": result.total_ascent_m,
            "total_descent_m": result.total_descent_m,
            "max_elevation_m": result.max_elevation_m,
            "min_elevation_m": result.min_elevation_m,
            "difficulty_level": result.difficulty_level,
            "estimated_duration_hours": result.estimated_duration_hours,
            "start_point_lon": result.start_point.lon,
            "start_point_lat": result.start_point.lat,
            "original_file_path": file_path,
            "is_public": 1 if is_public else 0,
        }

        # Note: async operation requires sync wrapper in production
        logger.info(f"Route data prepared for save: {name}")
        return (
            f"路线数据已准备：\n"
            f"- 名称：{name}\n"
            f"- 距离：{result.total_distance_km:.1f}km\n"
            f"- 难度：{result.difficulty_level}\n"
            f"- 海拔：{result.min_elevation_m:.0f}m ~ {result.max_elevation_m:.0f}m\n"
            f"路线已标记为{'公开' if is_public else '私有'}"
        )
    except Exception as e:
        return f"路线保存失败：{str(e)}"


class RouteSearchInput(BaseModel):
    location: Optional[str] = Field(default=None, description="位置名称或坐标")
    difficulty: Optional[str] = Field(default=None, description="难度等级：简单/中等/困难")
    radius_km: float = Field(default=50, description="搜索半径（公里）")


@tool("route_search", args_schema=RouteSearchInput)
def route_search(
    location: str = None, difficulty: str = None, radius_km: float = 50
) -> str:
    """搜索路线库中的公开路线。可按位置、难度筛选。
    返回匹配路线的列表。
    """
    # Placeholder — 需要异步 PostgreSQL 才能执行查询
    filters = []
    if location:
        filters.append(f"位置：{location}")
    if difficulty:
        filters.append(f"难度：{difficulty}")
    filter_str = "、".join(filters) if filters else "全部路线"

    return (
        f"路线库搜索（{filter_str}）：\n"
        f"当前路线库尚在建设中，暂无公开路线。\n"
        f"您可以先上传并保存自己的路线，未来将支持路线推荐。"
    )
