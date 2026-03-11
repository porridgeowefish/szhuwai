"""
Output Schemas
==============

Final delivery schemas for the Outdoor Activity Planner.
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Literal

from pydantic import BaseModel, Field, field_validator, ConfigDict

from .base import Point3D
from .track import TrackAnalysisResult
from .weather import WeatherSummary
from .transport import TransportRoutes
from .search import WebSearchResponse


class SafetyAssessment(BaseModel):
    """安全评估"""
    overall_risk: Optional[Literal["低风险", "中等风险", "高风险"]] = Field(None, description="总体风险等级")
    conditions: Optional[str] = Field(None, description="条件描述")
    recommendation: Optional[Literal["推荐", "谨慎推荐", "不推荐"]] = Field(None, description="推荐建议")
    risk_level: Optional[Literal["低风险", "中等风险", "高风险"]] = Field(None, description="风险等级")


class EmergencyContact(BaseModel):
    """紧急联系人"""
    name: str = Field(..., description="姓名/机构名称")
    phone: str = Field(..., description="电话号码")
    type: Optional[Literal["医疗", "救援", "旅游", "其他"]] = Field(None, description="联系人类型")


class LocalGuide(BaseModel):
    """当地向导"""
    name: str = Field(..., description="姓名")
    contact: str = Field(..., description="联系方式")
    experience: Optional[str] = Field(None, description="经验描述")
    rating: Optional[float] = Field(None, ge=0, le=5, description="评分")


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
    """户外活动计划最终交付物"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    # 基础信息
    plan_id: str = Field(..., description="计划ID")
    created_at: datetime = Field(default_factory=datetime.now)
    user_request: str = Field(..., description="用户原始请求")
    plan_name: str = Field(..., description="计划名称")

    # 轨迹信息
    track_analysis: TrackAnalysisResult = Field(..., description="轨迹分析结果")

    # 天气信息
    weather_info: WeatherSummary = Field(..., description="天气汇总")

    # 交通信息
    transport_info: TransportRoutes = Field(..., description="交通路线")

    # 搜索信息
    search_results: List[WebSearchResponse] = Field(default_factory=list, description="相关搜索结果")

    # 安全评估
    safety_assessment: SafetyAssessment = Field(default_factory=SafetyAssessment, description="综合安全评估")
    safety_issues: List[SafetyIssue] = Field(default_factory=list, description="安全问题列表")

    # 装备建议
    equipment_recommendations: List[EquipmentItem] = Field(default_factory=list, description="装备建议")

    # 注意事项
    precautions: List[str] = Field(default_factory=list, description="注意事项")

    # 最佳实践建议
    best_practices: List[str] = Field(default_factory=list, description="最佳实践")

    # 风景点推荐
    scenic_spots: List[ScenicSpot] = Field(default_factory=list, description="风景点推荐")

    # 总体评估
    overall_rating: Literal["推荐", "谨慎推荐", "不推荐"] = Field(..., description="总体推荐等级")
    confidence_score: float = Field(..., ge=0, le=1, description="方案可信度评分")
    risk_factors: List[str] = Field(default_factory=list, description="风险因素")

    # 推荐联系人
    emergency_contacts: List[EmergencyContact] = Field(default_factory=list, description="紧急联系人")
    local_guides: List[LocalGuide] = Field(default_factory=list, description="当地向导")

    # 行程安排
    itinerary: List[ItineraryItem] = Field(default_factory=list, description="行程安排")

    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_score(cls, v: float) -> float:
        """验证可信度评分在0到1之间"""
        if v < 0 or v > 1:
            raise ValueError("可信度评分必须在0到1之间")
        return v

    @property
    def total_equipment_weight(self) -> float:
        """总装备重量"""
        return sum(item.weight_kg or 0 for item in self.equipment_recommendations)

    @property
    def has_critical_safety_issues(self) -> bool:
        """是否存在关键安全问题"""
        return any(issue.severity in ["高", "极高"] for issue in self.safety_issues)

    @property
    def is_safe_plan(self) -> bool:
        """是否为安全计划"""
        return not self.has_critical_safety_issues and self.overall_rating != "不推荐"

    @property
    def required_equipment(self) -> List[EquipmentItem]:
        """必需装备"""
        return [item for item in self.equipment_recommendations if item.priority == "必需"]

    @property
    def recommended_equipment(self) -> List[EquipmentItem]:
        """推荐装备"""
        return [item for item in self.equipment_recommendations if item.priority == "推荐"]

    def get_equipment_by_category(self, category: EquipmentCategory) -> List[EquipmentItem]:
        """按类别获取装备"""
        return [item for item in self.equipment_recommendations if item.category == category]

    def get_safety_issues_by_type(self, issue_type: SafetyIssueType) -> List[SafetyIssue]:
        """按类型获取安全问题"""
        return [issue for issue in self.safety_issues if issue.type == issue_type]

    def get_top_scenic_spots(self, n: int = 3) -> List[ScenicSpot]:
        """获取前N个最佳风景点"""
        return sorted(self.scenic_spots,
                     key=lambda x: (x.is_worth_it, x.difficulty != "困难"),
                     reverse=True)[:n]

    def to_dict(self) -> Dict:
        """转换为字典"""
        return self.model_dump()

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return self.model_dump_json(indent=2, ensure_ascii=False)