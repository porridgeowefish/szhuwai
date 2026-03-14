"""
Weather API Schemas
===================

Schema definitions for weather data and forecasts following QWeather API specification.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class WeatherBaseDaily(BaseModel):
    """每日天气基础公共字段"""
    fxDate: str = Field(..., description="预报日期 YYYY-MM-DD")
    tempMax: int = Field(..., description="最高温度 (°C)")
    tempMin: int = Field(..., description="最低温度 (°C)")
    textDay: str = Field(..., description="白天天气状况描述")
    windScaleDay: str = Field(..., description="白天风力等级")
    windSpeedDay: int = Field(..., description="白天风速 (km/h)")
    humidity: int = Field(..., ge=0, le=100, description="相对湿度 (%)")
    precip: float = Field(..., ge=0, description="当天总降水量 (mm)")
    pressure: int = Field(..., description="大气压强 (hPa)")

    @field_validator('fxDate')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """验证日期格式为 YYYY-MM-DD"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('日期格式必须是 YYYY-MM-DD')


class CityWeatherDaily(WeatherBaseDaily):
    """城市每日天气契约"""
    uvIndex: Optional[int] = Field(None, ge=0, le=15, description="紫外线指数")
    vis: Optional[int] = Field(None, ge=0, description="能见度 (km)")
    cloud: Optional[int] = Field(None, ge=0, le=100, description="云量 (%)")
    sunrise: Optional[str] = Field(None, description="日出时间")
    sunset: Optional[str] = Field(None, description="日落时间")


class GridWeatherDaily(WeatherBaseDaily):
    """格点每日天气契约"""
    pass  # 仅继承基础数值模型字段


class HourlyWeather(BaseModel):
    """逐小时天气契约"""
    fxTime: str = Field(..., description="预报时间 (ISO 8601)")
    temp: int = Field(..., description="温度 (°C)")
    pop: int = Field(..., ge=0, le=100, description="降水概率 (%)")
    precip: float = Field(..., ge=0, description="降水量 (mm)")
    windScale: str = Field(..., description="风力等级")


class CityWeatherResponse(BaseModel):
    """城市天气预报响应"""
    location: str
    updateTime: str
    daily: List[CityWeatherDaily]

    @field_validator('updateTime')
    @classmethod
    def validate_datetime_format(cls, v: str) -> str:
        """验证时间格式"""
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            return v
        except ValueError:
            return v  # 允许其他格式


class GridWeatherResponse(BaseModel):
    """格点天气预报响应"""
    location: str
    updateTime: str
    daily: List[GridWeatherDaily]

    @field_validator('updateTime')
    @classmethod
    def validate_datetime_format(cls, v: str) -> str:
        """验证时间格式"""
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            return v
        except ValueError:
            return v  # 允许其他格式


class HourlyWeatherResponse(BaseModel):
    """逐小时天气预报响应"""
    location: str
    updateTime: str
    hourly: List[HourlyWeather]

    @field_validator('updateTime')
    @classmethod
    def validate_datetime_format(cls, v: str) -> str:
        """验证时间格式"""
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            return v
        except ValueError:
            return v  # 允许其他格式


class CurrentWeather(BaseModel):
    """当前天气"""
    temp: Optional[float] = Field(None, description="当前温度")
    text: Optional[str] = Field(None, description="天气描述")
    humidity: Optional[int] = Field(None, ge=0, le=100, description="相对湿度")
    wind_dir: Optional[str] = Field(None, description="风向")
    wind_scale: Optional[str] = Field(None, description="风力等级")


class WeatherSummaryInfo(BaseModel):
    """天气汇总信息"""
    conditions: Optional[str] = Field(None, description="天气条件描述")
    recommendation: Optional[str] = Field(None, description="推荐建议")
    risk_level: Optional[str] = Field(None, description="风险等级")


class WeatherSummary(BaseModel):
    """天气汇总"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    trip_date: str  # 出行日期
    forecast_days: int  # 预报天数
    use_grid: bool  # 是否使用格点天气
    warning: Optional[str] = None  # 警告信息
    current: Optional[CurrentWeather] = None  # 当前天气
    forecast_3d: Optional[CityWeatherResponse] = None  # 3天预报
    forecast_7d: Optional[CityWeatherResponse] = None  # 7天预报
    points_weather: List[Dict[str, Any]] = Field(default_factory=list)  # 各点天气
    summary: WeatherSummaryInfo = Field(
        default_factory=lambda: WeatherSummaryInfo(
            conditions=None,
            recommendation=None,
            risk_level=None
        ),
        description="汇总信息"
    )

    # 汇总字段
    max_temp: Optional[int] = None
    min_temp: Optional[int] = None
    best_cloud_sea_point: Optional[int] = None
    uv_analysis: Optional[str] = None
    precip_analysis: Optional[str] = None

    @field_validator('trip_date')
    @classmethod
    def validate_trip_date(cls, v: str) -> str:
        """验证出行日期格式为 YYYY-MM-DD"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('出行日期格式必须是 YYYY-MM-DD')

    @property
    def has_warning(self) -> bool:
        """是否有天气警告"""
        return self.warning is not None and self.warning.strip() != ''

    @property
    def temperature_range(self) -> Optional[int]:
        """温度范围"""
        if self.max_temp and self.min_temp:
            return self.max_temp - self.min_temp
        return None

    @property
    def safe_for_outdoor(self) -> bool:
        """是否适合户外活动"""
        if self.has_warning:
            return False

        # 检查温度范围
        if self.temperature_range and self.temperature_range > 30:
            return False

        # 检查是否有极端降水
        if self.forecast_3d:
            for day in self.forecast_3d.daily:
                if day.precip > 100:  # 暴雨
                    return False

        return True

    def get_daily_forecast(self, day_offset: int) -> Optional[CityWeatherDaily]:
        """获取指定天数后的预报"""
        if not self.forecast_3d and not self.forecast_7d:
            return None

        forecast = self.forecast_3d if day_offset <= 3 else self.forecast_7d
        if forecast and day_offset < len(forecast.daily):
            return forecast.daily[day_offset]
        return None


class CloudSeaAssessment(BaseModel):
    """云海评估"""
    score: Optional[int] = Field(None, ge=0, le=10, description="云海评分")
    level: Optional[str] = Field(None, description="云海等级")
    factors: List[str] = Field(default_factory=list, description="影响因素")


class WeatherCloudSeaAnalysis(BaseModel):
    """云海指数分析"""
    score: int = Field(..., ge=0, le=10)  # 云海评分 (0-10)
    level: str = Field(...)  # 云海等级
    factors: List[str] = Field(default_factory=list)  # 影响因素
    conditions: Dict[str, bool] = Field(default_factory=dict)  # 条件满足情况

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: int) -> int:
        """验证云海评分必须是 0, 3, 6, 9 或 10"""
        if v not in [0, 3, 6, 9, 10]:
            raise ValueError("云海评分必须是 0, 3, 6, 9 或 10")
        return v

    @model_validator(mode='before')
    @classmethod
    def set_level_by_score(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """根据评分自动设置云海等级"""
        if isinstance(data, dict):
            score = data.get('score')
            if score is not None and 'level' not in data:
                if score == 0:
                    data['level'] = "无云海"
                elif score <= 3:
                    data['level'] = "较差"
                elif score <= 6:
                    data['level'] = "一般"
                elif score <= 9:
                    data['level'] = "良好"
                else:
                    data['level'] = "极佳"
        return data


# 保持向后兼容的别名
WeatherGridPoint = CityWeatherDaily  # 向后兼容
WeatherGridResponse = CityWeatherResponse  # 向后兼容
WeatherDaily = CityWeatherDaily  # 向后兼容


def analyze_weather_safety(weather: CityWeatherResponse) -> Dict[str, Any]:
    """分析天气安全性"""
    safety_issues = []

    for day in weather.daily:
        # 高温警告
        if day.tempMax > 35:
            safety_issues.append(f"最高温度{day.tempMax}°C，有中暑风险")

        # 低温警告
        if day.tempMin < -10:
            safety_issues.append(f"最低温度{day.tempMin}°C，有冻伤风险")

        # 强风警告
        avg_wind_scale = int(day.windScaleDay[0]) if day.windScaleDay.isdigit() else 0
        if avg_wind_scale > 6:
            safety_issues.append(f"平均风力{avg_wind_scale}级，不适合户外活动")

        # 暴雨警告
        if day.precip > 50:
            safety_issues.append(f"预计降水量{day.precip}mm，有山洪风险")

        # 暴雪警告
        if '雪' in day.textDay and day.precip > 20:
            safety_issues.append(f"预计降雪{day.precip}mm，路滑危险")

    return {
        "is_safe": len(safety_issues) == 0,
        "safety_issues": safety_issues,
        "risk_level": "低风险" if len(safety_issues) == 0 else "高风险"
    }


def parse_wind_scale(wind_scale_str: str) -> int:
    """解析风力等级为数值"""
    if wind_scale_str.isdigit():
        return int(wind_scale_str)
    # 处理如 "3-4级" 的情况
    if '-' in wind_scale_str:
        return int(wind_scale_str.split('-')[0])
    return 0