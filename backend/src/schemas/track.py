"""
Track Analysis Schemas
=====================

Schema definitions for analyzing hiking tracks and trails.
"""

from datetime import datetime
from typing import List, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field, model_validator, ConfigDict

from .base import Point3D


class ElevationPoint(BaseModel):
    """海拔轨迹点（用于前端可视化）"""
    distance_m: float = Field(..., description="累计距离（米）")
    elevation_m: float = Field(..., description="海拔（米）")
    is_key_point: bool = Field(default=False, description="是否为关键点")
    label: Optional[str] = Field(None, description="关键点标签")


class TrackPointGCJ02(BaseModel):
    """轨迹点（GCJ02坐标系，用于高德地图显示）

    采用智能抽样策略：最多200点 + 关键点
    预估数据量 ≈ 10KB
    """
    lng: float = Field(..., description="经度（GCJ02坐标系）")
    lat: float = Field(..., description="纬度（GCJ02坐标系）")
    elevation: float = Field(default=0, description="海拔（米）")
    is_key_point: bool = Field(default=False, description="是否为关键点")
    label: Optional[str] = Field(None, description="关键点标签")


class TerrainChange(BaseModel):
    """地形变化段"""
    change_type: Literal["large_ascent", "large_descent"] = Field(..., description="Terrain change type")
    start_point: Point3D = Field(..., description="路段起点")
    end_point: Point3D = Field(..., description="路段终点")
    start_distance_m: float = Field(default=0, description="起点累计距离（米）")
    elevation_diff: float = Field(..., description="绝对上升/下降量 (米)", gt=0)
    distance_m: float = Field(..., description="该路段水平距离 (米)", gt=0)
    gradient_percent: float = Field(..., description="坡度 (百分比 %，如 15.5%)", ge=0)

    @model_validator(mode='before')
    @classmethod
    def calculate_gradient(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """自动计算坡度百分比"""
        if isinstance(data, dict):
            distance_m = data.get('distance_m')
            elevation_diff = data.get('elevation_diff')
            if distance_m is not None and elevation_diff is not None and distance_m > 0:
                # 计算坡度百分比：(垂直距离 / 水平距离) * 100
                data['gradient_percent'] = (elevation_diff / distance_m) * 100
        return data

    @property
    def duration_hours(self) -> float:
        """估算该路段用时（基于距离和坡度）"""
        # 基础速度：4km/h平地，坡度每增加10%减少0.5km/h
        base_speed = 4.0
        speed_reduction = (self.gradient_percent / 10) * 0.5
        speed = max(1.0, base_speed - speed_reduction)  # 最低1km/h
        return (self.distance_m / 1000) / speed


class TrackAnalysisResult(BaseModel):
    """轨迹分析结果"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    total_distance_km: float = Field(..., description="总里程 (公里)", gt=0)
    total_ascent_m: float = Field(..., description="总累计爬升 (米)", ge=0)
    total_descent_m: float = Field(..., description="总累计下降 (米)", ge=0)
    max_elevation_m: float = Field(..., description="最高海拔 (米)")
    min_elevation_m: float = Field(..., description="最低海拔 (米)")
    avg_elevation_m: float = Field(..., description="平均海拔 (米)")

    # 关键坐标点（用于后续调用天气和交通API）
    start_point: Point3D = Field(..., description="起步点")
    end_point: Point3D = Field(..., description="终点（如为环线则同起点）")
    max_elev_point: Point3D = Field(..., description="最高点（常用于查询极端风寒预报）")
    min_elev_point: Point3D = Field(..., description="最低点（用于查询最低气温）")

    # 核心业务逻辑：大爬升/大下降路段分析
    terrain_analysis: List[TerrainChange] = Field(default_factory=list, description="危险/高强度路段集合")

    # 海拔轨迹数据（用于前端可视化）
    elevation_points: List[ElevationPoint] = Field(default_factory=list, description="抽样海拔轨迹点")

    # 地图轨迹数据（GCJ02坐标系，用于高德地图平面图）
    track_points_gcj02: List[TrackPointGCJ02] = Field(
        default_factory=list,
        description="轨迹点（GCJ02坐标，智能抽样最多200点+关键点）"
    )

    # 路线评估指标
    difficulty_score: float = Field(..., description="难度评分 (0-100)", ge=0, le=100)
    difficulty_level: Literal["简单", "中等", "困难", "极难"] = Field(..., description="难度等级")
    estimated_duration_hours: float = Field(..., description="预计用时 (小时)", gt=0)
    safety_risk: Literal["低风险", "中等风险", "高风险", "极高风险"] = Field(..., description="安全风险等级")

    # 轨迹元数据
    track_name: Optional[str] = Field(None, description="轨迹名称")
    track_points_count: int = Field(..., description="轨迹点总数", gt=0)
    track_created_at: datetime = Field(default_factory=datetime.now, description="轨迹创建时间")

    @model_validator(mode='before')
    @classmethod
    def set_difficulty_level(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """根据难度评分自动设置难度等级"""
        if isinstance(data, dict):
            score = data.get('difficulty_score')
            if score is not None and 'difficulty_level' not in data:
                if score <= 25:
                    data['difficulty_level'] = "简单"
                elif score <= 50:
                    data['difficulty_level'] = "中等"
                elif score <= 75:
                    data['difficulty_level'] = "困难"
                else:
                    data['difficulty_level'] = "极难"
        return data

    @model_validator(mode='before')
    @classmethod
    def set_safety_risk(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """根据地形分析自动设置安全风险等级"""
        if isinstance(data, dict):
            terrain_analysis = data.get('terrain_analysis')
            if terrain_analysis is not None and 'safety_risk' not in data:
                intense_segments = len(terrain_analysis)
                if intense_segments == 0:
                    data['safety_risk'] = "低风险"
                elif intense_segments <= 2:
                    data['safety_risk'] = "中等风险"
                elif intense_segments <= 5:
                    data['safety_risk'] = "高风险"
                else:
                    data['safety_risk'] = "极高风险"
        return data

    @property
    def total_elevation_change(self) -> float:
        """总海拔变化"""
        return self.total_ascent_m + self.total_descent_m

    @property
    def elevation_range(self) -> float:
        """海拔范围"""
        return self.max_elevation_m - self.min_elevation_m

    def get_segment_warnings(self) -> List[str]:
        """获取路段警告信息"""
        warnings = []
        for i, segment in enumerate(self.terrain_analysis):
            if segment.change_type == "大爬升":
                warnings.append(f"第{i+1}段：大爬升{segment.elevation_diff:.0f}米，坡度{segment.gradient_percent:.1f}%")
            else:
                warnings.append(f"第{i+1}段：大下降{segment.elevation_diff:.0f}米，坡度{segment.gradient_percent:.1f}%")
        return warnings