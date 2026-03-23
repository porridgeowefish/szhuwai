"""
Output Schemas
==============

Final delivery schemas for the Outdoor Activity Planner.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal, Dict

from pydantic import BaseModel, Field, field_validator, ConfigDict

from .base import Point3D
from .track import TrackAnalysisResult
from .weather import WeatherSummary, CityWeatherDaily, HourlyWeather
from .transport import TransportRoutes
from .search import WebSearchResponse


class PlanningContext(BaseModel):
    """内部流转上下文模型（系统内部使用，不对外暴露）"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    # 原始请求
    raw_request: str = Field(..., description="用户原始请求")
    additional_info: str = Field(default="", description="用户额外要求/补充信息")

    # 精准位置名称（用于显示，不再用于搜索）
    precise_location_name: str = Field(default="", description="轨迹起点的精准位置名称")

    # 用户输入的线路信息（新增）
    plan_title: str = Field(default="", description="用户输入的线路名称/计划书标题")
    key_destinations: List[str] = Field(default_factory=list, description="用户输入的核心目的地列表")

    # 原始 API 数据
    track_analysis_raw: TrackAnalysisResult = Field(..., description="完整的轨迹分析结果")
    weather_raw: WeatherSummary = Field(..., description="完整的天气预报对象")
    transport_raw: TransportRoutes = Field(..., description="完整的交通API响应")
    search_raw: List[WebSearchResponse] = Field(default_factory=list, description="完整的网页搜索响应")

    # 高德周边救援数据（硬核数据，非 Web 搜索）
    around_rescue_data: List[Dict] = Field(default_factory=list, description="高德周边医院/派出所数据")

    # 可信度评分（内部打点使用）
    confidence_score: float = Field(..., ge=0, le=1, description="方案可信度评分")


class SafetyAssessment(BaseModel):
    """安全评估
    API 响应使用 camelCase 字段名（通过 alias 转换）。
    """
    model_config = ConfigDict(populate_by_name=True)

    overall_risk: Optional[Literal["低风险", "中等风险", "高风险"]] = Field(None, alias="overallRisk", description="总体风险等级")
    conditions: Optional[str] = Field(None, description="条件描述")
    recommendation: Optional[Literal["推荐", "谨慎推荐", "不推荐"]] = Field(None, description="推荐建议")
    risk_level: Optional[Literal["低风险", "中等风险", "高风险"]] = Field(None, alias="riskLevel", description="风险等级")


class EmergencyRescueContact(BaseModel):
    """公共救援/应急救援电话
    API 响应使用 camelCase 字段名（通过 alias 转换）。
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="救援机构名称")
    phone: str = Field(..., description="救援电话")
    type: Optional[Literal["医疗", "救援", "报警"]] = Field(None, description="救援类型")




class ItineraryItem(BaseModel):
    """行程安排项
    API 响应使用 camelCase 字段名（通过 alias 转换）。
    """
    model_config = ConfigDict(populate_by_name=True)

    time: str = Field(..., description="时间")
    activity: str = Field(..., description="活动内容")
    location: Optional[str] = Field(None, description="地点")
    duration_minutes: Optional[int] = Field(None, ge=0, alias="durationMinutes", description="预计时长（分钟）")
    notes: Optional[str] = Field(None, description="备注")


class EquipmentCategory(str, Enum):
    """装备类别"""
    CLOTHING = "服装"
    FOOTWEAR = "鞋类"
    BACKPACK = "背包"
    CAMPING = "露营装备"
    COOKING = "炊具"
    SAFETY = "安全装备"
    NAVIGATION = "导航工具"
    HYGIENE = "卫生用品"
    ELECTRONICS = "电子产品"
    MISC = "其他"


class EquipmentItem(BaseModel):
    """装备项
    API 响应使用 camelCase 字段名（通过 alias 转换）。
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="装备名称")
    category: EquipmentCategory = Field(..., description="类别")
    priority: Literal["必需", "推荐", "可选"] = Field(..., description="优先级")
    quantity: int = Field(default=1, ge=1, description="数量")
    weight_kg: Optional[float] = Field(None, ge=0, alias="weightKg", description="重量（千克）")
    description: Optional[str] = Field(None, description="描述说明")
    alternatives: List[str] = Field(default_factory=list, description="替代品")

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """验证数量必须大于0"""
        if v < 1:
            raise ValueError("数量必须大于0")
        return v


class SafetyIssueType(str, Enum):
    """安全问题类型"""
    WEATHER = "天气风险"
    TERRAIN = "地形风险"
    TRAFFIC = "交通风险"
    WILDLIFE = "野生动物风险"
    EMERGENCY = "紧急情况"
    EQUIPMENT = "装备风险"
    PHYSICAL = "身体条件风险"


class SafetyIssue(BaseModel):
    """安全问题"""
    type: SafetyIssueType = Field(..., description="问题类型")
    severity: Literal["低", "中", "高", "极高"] = Field(..., description="严重程度")
    description: str = Field(..., description="问题描述")
    mitigation: str = Field(..., description="缓解措施")
    emergency_contact: Optional[str] = Field(None, description="紧急联系方式")

    @field_validator('severity')
    @classmethod
    def set_severity_level(cls, v: str) -> str:
        """验证并设置严重程度级别"""
        if v in ["低", "中", "高", "极高"]:
            return v
        return "低"


class GridPointWeather(BaseModel):
    """关键格点天气（仅保留核心指标）
    API 响应使用 camelCase 字段名（通过 alias 转换）。
    """
    model_config = ConfigDict(populate_by_name=True)

    point_type: Literal["起点", "终点", "最高点", "中点"] = Field(..., alias="pointType")
    temp: int = Field(..., description="温度 (°C)")
    wind_scale: str = Field(..., alias="windScale", description="风力等级")
    humidity: int = Field(..., description="相对湿度 (%)")

    @field_validator('wind_scale', mode='before')
    @classmethod
    def convert_wind_scale_to_str(cls, v):
        """将风力等级转换为字符串"""
        if isinstance(v, int):
            return str(v)
        return v


class TerrainSegment(BaseModel):
    """地形分析路段
    API 响应使用 camelCase 字段名（通过 alias 转换）。
    """
    model_config = ConfigDict(populate_by_name=True)

    change_type: Literal["large_ascent", "large_descent"] = Field(..., alias="changeType", description="Terrain change type")
    elevation_diff: float = Field(..., alias="elevationDiff", description="海拔变化量 (米)")
    distance_m: float = Field(..., alias="distanceM", description="路段距离 (米)")
    gradient_percent: float = Field(..., alias="gradientPercent", description="坡度百分比")
    start_distance_m: float = Field(default=0, alias="startDistanceM", description="路段起点累计距离 (米)")


class ElevationPoint(BaseModel):
    """海拔轨迹点（用于前端可视化）
    API 响应使用 camelCase 字段名（通过 alias 转换）。
    """
    model_config = ConfigDict(populate_by_name=True)

    distance_m: float = Field(..., alias="distanceM", description="累计距离（米）")
    elevation_m: float = Field(..., alias="elevationM", description="海拔（米）")
    is_key_point: bool = Field(default=False, alias="isKeyPoint", description="是否为关键点")
    label: Optional[str] = Field(None, description="关键点标签")


class CloudSeaAssessment(BaseModel):
    """云海评估"""
    score: int = Field(default=0, ge=0, le=10, description="云海指数 (0-10)")
    level: str = Field(default="暂无数据", description="云海等级")
    factors: List[str] = Field(default_factory=list, description="影响因素")


class TrackDetailAnalysis(BaseModel):
    """轨迹详细分析
    API 响应使用 camelCase 字段名（通过 alias 转换）。
    """
    model_config = ConfigDict(populate_by_name=True)

    total_distance_km: float = Field(..., alias="totalDistanceKm", description="总里程 (公里)")
    total_ascent_m: float = Field(..., alias="totalAscentM", description="总累计爬升 (米)")
    total_descent_m: float = Field(..., alias="totalDescentM", description="总累计下降 (米)")
    max_elevation_m: float = Field(..., alias="maxElevationM", description="最高海拔 (米)")
    min_elevation_m: float = Field(..., alias="minElevationM", description="最低海拔 (米)")
    avg_elevation_m: float = Field(..., alias="avgElevationM", description="平均海拔 (米)")
    difficulty_level: str = Field(..., alias="difficultyLevel", description="难度等级")
    difficulty_score: float = Field(..., alias="difficultyScore", description="难度评分")
    estimated_duration_hours: float = Field(..., alias="estimatedDurationHours", description="预计用时 (小时)")
    safety_risk: str = Field(..., alias="safetyRisk", description="安全风险等级")
    terrain_analysis: List[TerrainSegment] = Field(default_factory=list, alias="terrainAnalysis", description="地形分析")
    elevation_points: List[ElevationPoint] = Field(default_factory=list, alias="elevationPoints", description="海拔轨迹点（用于前端可视化）")
    cloud_sea_assessment: Optional[CloudSeaAssessment] = Field(None, alias="cloudSeaAssessment", description="云海评估")


class ScenicSpot(BaseModel):
    """风景点 - 以科普和故事为核心，激发用户探索兴趣
    API 响应使用 camelCase 字段名（通过 alias 转换）。
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="景点名称")
    spot_type: Literal["自然风光", "人文景观"] = Field(..., alias="spotType", description="景点类型")
    description: str = Field(..., description="景点描述（自然风光需科学科普，人文景观需讲述背后故事）")
    location: Point3D = Field(..., description="景点位置坐标")


class OutdoorActivityPlan(BaseModel):
    """户外活动计划最终交付物（轻量化 View 模型）
    API 响应使用 camelCase 字段名（通过 alias 转换）。
    """
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    # 1. 基础信息
    plan_id: str = Field(..., alias="planId", description="计划ID")
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")
    plan_name: str = Field(..., alias="planName", description="计划名称")
    overall_rating: Literal["推荐", "谨慎推荐", "不推荐"] = Field(..., alias="overallRating", description="总体推荐等级")

    # 2. 文本概述（由 LLM 基于 Context 提炼）
    track_overview: str = Field(..., alias="trackOverview", description="轨迹概述，如：11km/爬升750m/困难")
    weather_overview: str = Field(..., alias="weatherOverview", description="天气概述，如：周末晴朗，最高25度，无降水风险")
    transport_overview: str = Field(..., alias="transportOverview", description="交通概述，如：建议驾车，约1.5小时")

    # 3. 精准保留的天气数据（用于前端 UI 渲染）
    trip_date_weather: CityWeatherDaily = Field(..., alias="tripDateWeather", description="出行当天的详细天气")
    hourly_weather: List[HourlyWeather] = Field(default_factory=list, alias="hourlyWeather", description="出行的逐小时天气预报")
    critical_grid_weather: List[GridPointWeather] = Field(default_factory=list, alias="criticalGridWeather", description="起点、终点、最高点的格点天气简报")

    # 4. 核心规划内容
    itinerary: List[ItineraryItem] = Field(default_factory=list, description="行程安排")
    equipment_recommendations: List[EquipmentItem] = Field(default_factory=list, alias="equipmentRecommendations", description="装备建议")
    scenic_spots: List[ScenicSpot] = Field(default_factory=list, alias="scenicSpots", description="风景点推荐")
    precautions: List[str] = Field(default_factory=list, description="注意事项")
    hiking_advice: str = Field(default="", alias="hikingAdvice", description="徒步建议（AI生成的综合建议，以叙事方式呈现）")

    # 5. 安全与应急
    safety_assessment: SafetyAssessment = Field(
        default_factory=lambda: SafetyAssessment(
            overall_risk=None,
            conditions=None,
            recommendation=None,
            risk_level=None
        ),
        alias="safetyAssessment",
        description="综合安全评估"
    )
    safety_issues: List[SafetyIssue] = Field(default_factory=list, alias="safetyIssues", description="具体安全风险点")
    risk_factors: List[str] = Field(default_factory=list, alias="riskFactors", description="风险因素标签")
    emergency_rescue_contacts: List[EmergencyRescueContact] = Field(default_factory=list, alias="emergencyRescueContacts", description="公共/应急救援电话")

    # 6. 轨迹详细分析
    track_detail: Optional[TrackDetailAnalysis] = Field(None, alias="trackDetail", description="轨迹详细分析数据")

    # 7. 交通方案详情
    transport_scheme: Optional[TransportRoutes] = Field(None, alias="transportScheme", description="交通方案详情（多种交通方式）")