"""
Output Schemas
==============

Final delivery schemas for the Outdoor Activity Planner.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal

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

    # 原始 API 数据
    track_analysis_raw: TrackAnalysisResult = Field(..., description="完整的轨迹分析结果")
    weather_raw: WeatherSummary = Field(..., description="完整的天气预报对象")
    transport_raw: TransportRoutes = Field(..., description="完整的交通API响应")
    search_raw: List[WebSearchResponse] = Field(default_factory=list, description="完整的网页搜索响应")

    # 可信度评分（内部打点使用）
    confidence_score: float = Field(..., ge=0, le=1, description="方案可信度评分")


class SafetyAssessment(BaseModel):
    """安全评估"""
    overall_risk: Optional[Literal["低风险", "中等风险", "高风险"]] = Field(None, description="总体风险等级")
    conditions: Optional[str] = Field(None, description="条件描述")
    recommendation: Optional[Literal["推荐", "谨慎推荐", "不推荐"]] = Field(None, description="推荐建议")
    risk_level: Optional[Literal["低风险", "中等风险", "高风险"]] = Field(None, description="风险等级")


class EmergencyRescueContact(BaseModel):
    """公共救援/应急救援电话"""
    name: str = Field(..., description="救援机构名称")
    phone: str = Field(..., description="救援电话")
    type: Optional[Literal["医疗", "救援", "报警"]] = Field(None, description="救援类型")




class ItineraryItem(BaseModel):
    """行程安排项"""
    time: str = Field(..., description="时间")
    activity: str = Field(..., description="活动内容")
    location: Optional[str] = Field(None, description="地点")
    duration_minutes: Optional[int] = Field(None, ge=0, description="预计时长（分钟）")
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
    """装备项"""
    name: str = Field(..., description="装备名称")
    category: EquipmentCategory = Field(..., description="类别")
    priority: Literal["必需", "推荐", "可选"] = Field(..., description="优先级")
    quantity: int = Field(default=1, ge=1, description="数量")
    weight_kg: Optional[float] = Field(None, ge=0, description="重量（千克）")
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
    """关键格点天气（仅保留核心指标）"""
    point_type: Literal["起点", "终点", "最高点"]
    temp: int = Field(..., description="温度 (°C)")
    wind_scale: str = Field(..., description="风力等级")
    humidity: int = Field(..., description="相对湿度 (%)")


class ScenicSpot(BaseModel):
    """风景点"""
    name: str = Field(..., description="景点名称")
    description: str = Field(..., description="景点描述")
    location: Point3D = Field(..., description="景点位置")
    best_view_time: Optional[str] = Field(None, description="最佳观赏时间")
    photo_spots: List[str] = Field(default_factory=list, description="摄影点")
    difficulty: Literal["简单", "中等", "困难"] = Field(default="中等", description="到达难度")
    estimated_visit_time_min: int = Field(default=30, ge=0, description="预计游览时间（分钟）")

    @property
    def is_worth_it(self) -> bool:
        """是否值得推荐"""
        return len(self.photo_spots) > 0 and self.difficulty != "困难"


class OutdoorActivityPlan(BaseModel):
    """户外活动计划最终交付物（轻量化 View 模型）"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    # 1. 基础信息
    plan_id: str = Field(..., description="计划ID")
    created_at: datetime = Field(default_factory=datetime.now)
    plan_name: str = Field(..., description="计划名称")
    overall_rating: Literal["推荐", "谨慎推荐", "不推荐"] = Field(..., description="总体推荐等级")

    # 2. 文本概述（由 LLM 基于 Context 提炼）
    track_overview: str = Field(..., description="轨迹概述，如：11km/爬升750m/困难")
    weather_overview: str = Field(..., description="天气概述，如：周末晴朗，最高25度，无降水风险")
    transport_overview: str = Field(..., description="交通概述，如：建议驾车，约1.5小时")

    # 3. 精准保留的天气数据（用于前端 UI 渲染）
    trip_date_weather: CityWeatherDaily = Field(..., description="出行当天的详细天气")
    hourly_weather: List[HourlyWeather] = Field(default_factory=list, description="出行的逐小时天气预报")
    critical_grid_weather: List[GridPointWeather] = Field(default_factory=list, description="起点、终点、最高点的格点天气简报")

    # 4. 核心规划内容
    itinerary: List[ItineraryItem] = Field(default_factory=list, description="行程安排")
    equipment_recommendations: List[EquipmentItem] = Field(default_factory=list, description="装备建议")
    scenic_spots: List[ScenicSpot] = Field(default_factory=list, description="风景点推荐")
    precautions: List[str] = Field(default_factory=list, description="注意事项")

    # 5. 安全与应急
    safety_assessment: SafetyAssessment = Field(default_factory=lambda: SafetyAssessment(), description="综合安全评估")
    safety_issues: List[SafetyIssue] = Field(default_factory=list, description="具体安全风险点")
    risk_factors: List[str] = Field(default_factory=list, description="风险因素标签")
    emergency_rescue_contacts: List[EmergencyRescueContact] = Field(default_factory=list, description="公共/应急救援电话")