"""
Transport API Schemas
====================

Schema definitions for map routing and transportation data.
"""

from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator

from .base import Point3D


class LocationInfo(BaseModel):
    """位置信息"""
    address: str = Field(..., description="地址")
    lat: Optional[float] = Field(None, description="纬度")
    lon: Optional[float] = Field(None, description="经度")
    adcode: Optional[str] = Field(None, description="行政区划代码")
    city: Optional[str] = Field(None, description="城市")
    province: Optional[str] = Field(None, description="省份")


class RouteSummary(BaseModel):
    """路线汇总信息"""
    total_distance: Optional[str] = Field(None, description="总距离描述")
    total_time: Optional[str] = Field(None, description="总时间描述")
    cost: Optional[str] = Field(None, description="费用描述")
    fastest_mode: Optional[str] = Field(None, description="最快方式")
    cheapest_mode: Optional[str] = Field(None, description="最便宜方式")


class RouteStep(BaseModel):
    """路线步骤"""
    instruction: str  # 指导说明
    distance: float = Field(..., ge=0, description="距离（米）")
    duration: int = Field(..., ge=0, description="时长（秒）")
    orientation: Optional[str] = None  # 朝向
    road_name: Optional[str] = None  # 道路名称

    @property
    def duration_minutes(self) -> float:
        """时长（分钟）"""
        return self.duration / 60


class TransitSegment(BaseModel):
    """公交段"""
    type: str = Field(..., description="交通类型 (subway, bus, walk)")
    line_name: str = Field(..., description="线路名称（如'地铁4号线大兴线'、'特8路'）")
    line_id: Optional[str] = Field(None, description="线路ID")
    departure_stop: str = Field(..., description="上车站名称")
    arrival_stop: str = Field(..., description="下车站名称")
    duration_min: int = Field(..., ge=0, description="时长（分钟）")
    distance_m: int = Field(..., ge=0, description="距离（米）")
    price_yuan: int = Field(..., ge=0, description="价格（元）")
    operator: Optional[str] = Field(None, description="运营方")


class TransitRoute(BaseModel):
    """公交路线（简化版，仅返回核心信息）"""
    available: bool = Field(..., description="是否有可用路线")
    duration_min: int = Field(..., ge=0, description="时长（分钟）")
    distance_km: float = Field(..., ge=0, description="距离（公里）")
    cost_yuan: int = Field(..., ge=0, description="费用（元）")
    walking_distance: int = Field(..., ge=0, description="步行距离（米）")
    segments: Optional[List[TransitSegment]] = Field(None, description="公交段详细信息")
    line_name: Optional[str] = Field(None, description="主要线路名称")
    departure_stop: Optional[str] = Field(None, description="上车点")
    arrival_stop: Optional[str] = Field(None, description="下车点")

    @field_validator('duration_min')
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """验证时长非负"""
        if v < 0:
            raise ValueError("时长不能为负数")
        return v

    @property
    def is_reasonable(self) -> bool:
        """判断是否合理（步行距离不超过2km，时间不超过3小时）"""
        return self.walking_distance <= 2000 and self.duration_min <= 180


class TransitRouteDetail(BaseModel):
    """详细的公交路线（包含多条方案）"""
    routes: List[TransitRoute] = Field(..., description="公交路线列表，最多3条")
    taxi_cost_yuan: Optional[int] = Field(None, description="打车费用预估（元）")
    walking_distance_m: int = Field(0, description="总步行距离")


class DrivingRoute(BaseModel):
    """驾车路线（简化版，仅返回核心信息）"""
    available: bool = Field(..., description="是否有可用路线")
    duration_min: int = Field(..., ge=0, description="时长（分钟）")
    distance_km: float = Field(..., ge=0, description="距离（公里）")
    tolls_yuan: int = Field(..., ge=0, description="过路费（元）")

    @property
    def cost_per_km(self) -> float:
        """每公里成本"""
        if self.distance_km > 0:
            return (self.tolls_yuan / self.distance_km)
        return 0


class WalkingRoute(BaseModel):
    """步行路线（简化版，仅返回核心信息）"""
    available: bool = Field(..., description="是否有可用路线")
    duration_min: int = Field(..., ge=0, description="时长（分钟）")
    distance_m: int = Field(..., ge=0, description="距离（米）")

    @property
    def is_feasible(self) -> bool:
        """判断是否可行（距离不超过20km，时间不超过5小时）"""
        return self.distance_m <= 20000 and self.duration_min <= 300


class TransportRoutes(BaseModel):
    """综合交通路线"""
    origin: LocationInfo = Field(..., description="起点信息")
    destination: LocationInfo = Field(..., description="终点信息")
    outbound: Dict[str, Any] = Field(..., description="去程路线")
    return_route: Dict[str, Any] = Field(default_factory=dict, description="返程路线")
    summary: RouteSummary = Field(
        default_factory=lambda: RouteSummary(
            total_distance=None,
            total_time=None,
            cost=None,
            fastest_mode=None,
            cheapest_mode=None
        ),
        description="汇总信息"
    )

    # 推荐方案
    recommended_mode: Optional[str] = Field(None, description="推荐交通方式")
    fastest_mode: Optional[str] = Field(None, description="最快交通方式")
    cheapest_mode: Optional[str] = Field(None, description="最便宜交通方式")

    # 打车费用
    taxi_cost_yuan: Optional[int] = Field(None, description="打车费用预估（元）")

    @property
    def has_return_route(self) -> bool:
        """是否有返程路线"""
        return bool(self.return_route)

    def get_route_by_mode(self, mode: str) -> Optional[Dict[str, Any]]:
        """根据交通方式获取路线"""
        if mode == 'outbound':
            return self.outbound
        elif mode == 'return' and self.has_return_route:
            return self.return_route
        return None

    def get_all_modes(self) -> List[str]:
        """获取所有可用的交通方式"""
        modes = ['outbound']
        if self.has_return_route:
            modes.append('return')
        return modes


class GeocodeResult(BaseModel):
    """地理编码结果"""
    address: str = Field(..., description="地址")
    province: str = Field(..., description="省份")
    city: str = Field(..., description="城市")
    district: str = Field(..., description="区县")
    street: Optional[str] = Field(None, description="街道")
    adcode: str = Field(..., description="行政区划代码")
    lon: float = Field(..., description="经度", ge=-180, le=180)
    lat: float = Field(..., description="纬度", ge=-90, le=90)

    @field_validator('street')
    @classmethod
    def validate_street(cls, v: Optional[List[str]]) -> Optional[str]:
        """验证街道字段"""
        if isinstance(v, list):
            return v[0] if v else None
        return v

    @field_validator('adcode')
    @classmethod
    def validate_adcode(cls, v: str) -> str:
        """验证行政区划代码格式"""
        if not v.isdigit() or len(v) not in [6, 12]:
            raise ValueError("行政区划代码必须是6位或12位数字")
        return v

    def to_point3d(self, elevation: float = 0) -> Point3D:
        """转换为3D坐标点"""
        return Point3D(
            lat=self.lat,
            lon=self.lon,
            elevation=elevation,
            timestamp=None
        )


class ReverseGeocodeResult(BaseModel):
    """逆地理编码结果"""
    address: str = Field(..., description="地址")
    province: str = Field(..., description="省份")
    city: str = Field(..., description="城市")
    district: str = Field(..., description="区县")
    adcode: str = Field(..., description="行政区划代码")
    township: Optional[str] = Field(None, description="乡镇")
    street_number: Optional[str] = Field(None, description="门牌号")
    building: Optional[str] = Field(None, description="建筑物")
    lon: float = Field(..., description="经度", ge=-180, le=180)
    lat: float = Field(..., description="纬度", ge=-90, le=90)

    @field_validator('adcode')
    @classmethod
    def validate_adcode(cls, v: str) -> str:
        """验证行政区划代码格式"""
        if not v.isdigit() or len(v) not in [6, 12]:
            raise ValueError("行政区划代码必须是6位或12位数字")
        return v

    def to_point3d(self, elevation: float = 0) -> Point3D:
        """转换为3D坐标点"""
        return Point3D(
            lat=self.lat,
            lon=self.lon,
            elevation=elevation,
            timestamp=None
        )

    @property
    def full_address(self) -> str:
        """完整地址"""
        parts = [self.address, self.province, self.city, self.district]
        if self.township:
            parts.append(self.township)
        if self.street_number:
            parts.append(self.street_number)
        return ' '.join(filter(None, parts))