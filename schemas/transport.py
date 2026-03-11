"""
Transport API Schemas
====================

Schema definitions for map routing and transportation data.
"""

from typing import Optional, List, Literal, Dict

from pydantic import BaseModel, Field, field_validator, ConfigDict

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
    action: str  # 动作类型
    orientation: Optional[str] = None  # 朝向
    road_name: Optional[str] = None  # 道路名称

    @property
    def duration_minutes(self) -> float:
        """时长（分钟）"""
        return self.duration / 60


class TransitRoute(BaseModel):
    """公交路线"""
    available: bool = Field(..., description="是否有可用路线")
    duration_min: int = Field(..., ge=0, description="时长（分钟）")
    distance_km: float = Field(..., ge=0, description="距离（公里）")
    cost_yuan: int = Field(..., ge=0, description="费用（元）")
    walking_distance: int = Field(..., ge=0, description="步行距离（米）")
    steps: List[RouteStep] = Field(default_factory=list, description="路线步骤")

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


class DrivingRoute(BaseModel):
    """驾车路线"""
    available: bool = Field(..., description="是否有可用路线")
    duration_min: int = Field(..., ge=0, description="时长（分钟）")
    distance_km: float = Field(..., ge=0, description="距离（公里）")
    tolls_yuan: int = Field(..., ge=0, description="过路费（元）")
    traffic_lights: int = Field(..., ge=0, description="红绿灯数量")
    steps: List[RouteStep] = Field(default_factory=list, description="路线步骤")

    @property
    def cost_per_km(self) -> float:
        """每公里成本"""
        if self.distance_km > 0:
            return (self.tolls_yuan / self.distance_km)
        return 0


class WalkingRoute(BaseModel):
    """步行路线"""
    available: bool = Field(..., description="是否有可用路线")
    duration_min: int = Field(..., ge=0, description="时长（分钟）")
    distance_m: int = Field(..., ge=0, description="距离（米）")
    steps: List[RouteStep] = Field(default_factory=list, description="路线步骤")

    @property
    def is_feasible(self) -> bool:
        """判断是否可行（距离不超过20km，时间不超过5小时）"""
        return self.distance_m <= 20000 and self.duration_min <= 300


class TransportRoutes(BaseModel):
    """综合交通路线"""
    origin: LocationInfo = Field(..., description="起点信息")
    destination: LocationInfo = Field(..., description="终点信息")
    outbound: Dict = Field(..., description="去程路线")
    return_route: Dict = Field(default_factory=dict, description="返程路线")
    summary: RouteSummary = Field(default_factory=RouteSummary, description="汇总信息")

    # 推荐方案
    recommended_mode: Optional[str] = Field(None, description="推荐交通方式")
    fastest_mode: Optional[str] = Field(None, description="最快交通方式")
    cheapest_mode: Optional[str] = Field(None, description="最便宜交通方式")

    @property
    def has_return_route(self) -> bool:
        """是否有返程路线"""
        return bool(self.return_route)

    def get_route_by_mode(self, mode: str) -> Optional[Dict]:
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
            elevation=elevation
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
            elevation=elevation
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